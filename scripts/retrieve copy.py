#!/usr/bin/env python
"""
run_findscu.py

- findscu 실행 결과와 PDU 덤프를 콘솔에 출력
- audit_events 테이블에 C-FIND/C-MOVE 이벤트를 기록
- PDU 덤프(stdout, stderr)는 modality별 파일로 저장
- 추출된 StudyInstanceUID 리스트를 다음 단계인 movescu로 전달
"""

import re
import subprocess
import psycopg2
import json
from pathlib import Path
from datetime import datetime

from nmdose import (
    get_config,
    get_pacs_config,
    get_retrieve_config,
    get_schedule_config,
    get_db_config,
    make_batch_date_range,
    sanitize_event
)

def insert_audit_event(conn, event):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO findscus
              (ts, event_type, calling_aet, called_aet,
               peer_host, peer_port, filters, result_count,
               duration_ms, status, error_detail, study_instance_uid)
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
        """, (
            event["ts"],
            event["event_type"],
            event["calling_aet"],
            event["called_aet"],
            event["peer_host"],
            event["peer_port"],
            json.dumps(event["filters"]),
            event["result_count"],
            event["duration_ms"],
            event["status"],
            event["error_detail"],
            event["study_instance_uid"]
        ))
    conn.commit()

def run_findscu_and_move():
    # 1) Load configurations
    cfg = get_config()
    pacs = get_pacs_config()
    rcfg = get_retrieve_config()
    sched = get_schedule_config()

    # 2) Choose PACS source/target
    if cfg.running_mode.lower() == "simulation":
        source, target = pacs.research, pacs.simulation
    else:
        source, target = pacs.research, pacs.clinical

    # 3) Compute date range and modalities
    date_range = make_batch_date_range()
    modalities = rcfg.clinical_to_research.modalities

    # 4) Prepare log directory
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # 5) Open DB connection for auditing
    db_conf = get_db_config().rpacs
    conn = psycopg2.connect(
        host=db_conf.host,
        port=db_conf.port,
        dbname=db_conf.database,
        user=db_conf.user,
        password=db_conf.user
    )

    all_uids = []
    for modality in modalities:
        print(f"\\n=== Modality: {modality} ===")

        cmd = [
            "findscu", "-v", "-S",
            "-aet", source.aet,
            "-aec", target.aet, target.ip, str(target.port),
            "-k", "QueryRetrieveLevel=STUDY",
            "-k", f"StudyDate={date_range}",
            "-k", f"ModalitiesInStudy={modality}",
            "-k", "StudyInstanceUID="
        ]
        print("▶ C-FIND:", " ".join(cmd))

        ts_start = datetime.now()
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            stdout_text = result.stdout
            stderr_text = result.stderr
            status = "SUCCESS"
        except subprocess.CalledProcessError as e:
            stdout_text = e.stdout or ""
            stderr_text = e.stderr or ""
            status = "FAILURE"
        ts_end = datetime.now()
        duration_ms = int((ts_end - ts_start).total_seconds() * 1000)

        # Save logs
        ts_str = ts_start.strftime("%Y%m%d_%H%M%S")
        stdout_file = log_dir / f"findscu_stdout_{modality}_{ts_str}.log"
        stderr_file = log_dir / f"findscu_stderr_{modality}_{ts_str}.log"
        stdout_file.write_text(stdout_text, encoding="utf-8")
        stderr_file.write_text(stderr_text, encoding="utf-8")
        print(f"  STDOUT → {stdout_file}")
        print(f"  STDERR → {stderr_file}")

        # Extract UIDs
        uids = re.findall(r'\(0020,000d\) UI \[([^\]]+)\]', stderr_text)
        
        print(f"  Found {len(uids)} UIDs")
        all_uids.extend(uids)

        # Audit C-FIND event
        event = {
            "ts": ts_start,
            "calling_aet": source.aet,
            "called_aet": target.aet,
            "peer_host": target.ip,
            "peer_port": target.port,
            "query_retrieve_level": "study",
            "modalities_in_study": modality,
            "result_count": len(uids),
            "duration_ms": duration_ms,
            "status": status,
            "error_detail": stderr_text.strip() or None,
        }

        sanitize_event(event)
                      
        insert_audit_event(conn, event)


     # C-MOVE for unique UIDs
    unique_uids = list(dict.fromkeys(all_uids))
    for uid in unique_uids:
        i=1
        print(i)
        i+=1
        clean_uid = uid.replace("\x00", "")
        move_cmd = [
            "movescu", "-v",
            "-aet", source.aet,
            "-aec", target.aet, target.ip, str(target.port),
            "-k", "QueryRetrieveLevel=STUDY",
            "-k", f"StudyInstanceUID={clean_uid}"
        ]
        print("▶ C-MOVE:", " ".join(move_cmd))
        ts_mv_start = datetime.now()
        try:
            result=subprocess.run(move_cmd, check=True)
            stdout_mv_text = result.stdout
            stderr_mv_text = result.stderr
            mv_status = "SUCCESS"
        except subprocess.CalledProcessError as e:
            mv_status = "FAILURE"
            print(f"  ❗ C-MOVE failed for UID {uid}: {e}")
        ts_mv_end = datetime.now()
        mv_duration = int((ts_mv_end - ts_mv_start).total_seconds() * 1000)
        # Save logs
        ts_mv_str = ts_mv_start.strftime("%Y%m%d_%H%M%S")
        stdout_file = log_dir / f"movescu_stdout_{ts_mv_str}.log"
        stderr_file = log_dir / f"movescu_stderr_{ts_mv_str}.log"
        stdout_file.write_text(stdout_mv_text, encoding="utf-8")
        stderr_file.write_text(stderr_mv_text, encoding="utf-8")
        print(f"  STDOUT → {stdout_file}")
        print(f"  STDERR → {stderr_file}")

        

        # Audit C-MOVE event
        event_move = {
            "ts": ts_mv_start,
            "event_type": "C_MOVE",
            "calling_aet": source.aet,
            "called_aet": target.aet,
            "peer_host": target.ip,
            "peer_port": target.port,
            "filters": {"StudyInstanceUID": uid.replace("\x00", "")},
            "result_count": 1,
            "duration_ms": mv_duration,
            "status": mv_status,
            "error_detail": None,
            "study_instance_uid": uid.replace("\x00", "")
        }

# Remove NUL characters
        sanitize_event(event_move)

        insert_audit_event(conn, event_move)

    conn.close()

if __name__ == "__main__":
    run_findscu_and_move()

