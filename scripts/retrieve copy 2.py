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
    parse_start_date,
    parse_end_date,
    sanitize_event
)

# ─── 환경 초기화 ────────────────────────────────────────────────────────────
def init_environment():
    cfg     = get_config()
    pacs    = get_pacs_config()
    rcfg    = get_retrieve_config()
    sched   = get_schedule_config()
    db_conf = get_db_config().rpacs
    conn = psycopg2.connect(
        dbname=db_conf.database,
        user=db_conf.user,
        password=db_conf.user,
        host=db_conf.host,
        port=db_conf.port
    )
    log_dir = Path(r"C:\nmdose\logs\batch")
    log_dir.mkdir(parents=True, exist_ok=True)
    return cfg, pacs, rcfg, sched, conn, log_dir

# ─── PACS 선택 ──────────────────────────────────────────────────────────────
def select_pacs(cfg, pacs):
    if cfg.running_mode.lower() == "simulation":
        return pacs.research, pacs.simulation
    else:
        return pacs.research, pacs.clinical

# ─── 서브프로세스 실행 ──────────────────────────────────────────────────────
def run_process(cmd: list[str]) -> tuple[str, str]:
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        std_combined_text = result.stdout or "" + result.stderr or ""
        status = "SUCCESS"
    except subprocess.CalledProcessError as e:
        std_combined_text = e.stdout or "" + e.stderr or ""
        status = "FAILURE"
    return std_combined_text, status

# ─── 로그 파일, 저장 ──────────────────────────────────────────────────────────
def save_logs(log_dir, mode, modality: str, ts_start: datetime, std_combined_text, uid):
    ts_str = ts_start.strftime("%Y%m%d_%H%M%S")
    sanitized_text = std_combined_text.replace("\x00", "")
    clean_uid = uid.replace("\x00", "")
    std_combined_file = log_dir / f"{mode}_std_combined_{modality}_{ts_str}_{clean_uid}.log"
    std_combined_file.write_text(sanitized_text, encoding="utf-8")
    print(f"  STD_Combined → {std_combined_file}")


def insert_findscus (conn, event):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO findscus
              (ts, calling_aet, called_aet, peer_host, peer_port, query_retrieve_level, start_date, end_date, 
                    modalities_in_study, result_count, duration_ms, status, error_detail)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event["ts"],
            event["calling_aet"],
            event["called_aet"],
            event["peer_host"],
            event["peer_port"],
            event["query_retrieve_level"],
            event["start_date"],
            event["end_date"],
            event["modalities_in_study"],
            event["result_count"],
            event["duration_ms"],
            event["status"],
            event["error_detail"],
        ))
    conn.commit()

def insert_movescus (conn, event):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO findscus
              (ts, calling_aet, called_aet, peer_host, peer_port, pending_count, duration_ms, status, error_detail, study_instance_uid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
        """, (
            event["ts"],
            event["calling_aet"],
            event["called_aet"],
            event["peer_host"],
            event["peer_port"],
            event["pending_count"],
            event["duration_ms"],
            event["status"],
            event["error_detail"],
            event["study_instance_uid"],
        ))
    conn.commit()    

def run_retrieve():
    # 1) Load configurations
    cfg, pacs, rcfg, sched, conn, log_dir = init_environment()
    # 2) Choose PACS source/target
    source, target = select_pacs(cfg, pacs)
    # 3) Compute date range and modalities
    date_range = make_batch_date_range()
    # 4) modalities
    modalities = rcfg.clinical_to_research.modalities
    # 5) findscu
    

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
        std_combined_text, status = run_process(cmd)
        ts_end = datetime.now()
        duration_ms = int((ts_end - ts_start).total_seconds() * 1000)

        save_logs (log_dir, "findscu", modality, ts_start, std_combined_text, "uid")
     
        # Extract UIDs
        uids = re.findall(r'\(0020,000d\) UI \[([^\]]+)\]', std_combined_text)
        
        print(f"  Found {len(uids)} UIDs")
        all_uids.extend(uids)

        # Audit C-FIND event
        event = {
            "ts": ts_start,
            "calling_aet": source.aet,
            "called_aet": target.aet,
            "peer_host": target.ip,
            "peer_port": target.port,
            "query_retrieve_level": "STUDY",
            "start_date": parse_start_date(date_range),
            "end_date": parse_end_date(date_range),
            "modaliities_in_study": modality,
            "result_count": len(uids),
            "duration_ms": duration_ms,
            "status": status,
            "error_detail": std_combined_text.strip() or None,
        }

        sanitize_event(event)
                      
        insert_findscus(conn, event)


     # C-MOVE for unique UIDs
    unique_uids = list(dict.fromkeys(all_uids))
    for uid in unique_uids:
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
        mv_std_combined_text, mv_status = run_process(move_cmd)
        ts_mv_end = datetime.now()
        mv_duration = int((ts_mv_end - ts_mv_start).total_seconds() * 1000)

        save_logs (log_dir, "movescu", "ALL_MODALITY", ts_mv_start, mv_std_combined_text, uid)
             

        # Audit C-MOVE event
        event_move = {
            "find_id": None,
            "ts": ts_mv_start,
            "calling_aet": source.aet,
            "called_aet": target.aet,
            "peer_host": target.ip,
            "peer_port": target.port,
            "pending_count": 3,
            "duration_ms": mv_duration,
            "status": mv_status,
            "error_detail": mv_std_combined_text,
            "study_instance_uid": uid.replace("\x00", "")
        }

# Remove NUL characters
        sanitize_event(event_move)

        insert_movescus(conn, event_move)

    conn.close()

if __name__ == "__main__":
    run_retrieve()

