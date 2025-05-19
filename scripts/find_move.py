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
import sys
import psycopg2
import json
from pathlib import Path

# src 폴더를 sys.path에 추가
project_root = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(project_root))


from datetime import datetime, date

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
    CONFIG     = get_config()
    PACS    = get_pacs_config()
    RETRIEVE_CONFIG    = get_retrieve_config()
    SCHEDULE_CONFIG   = get_schedule_config()
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
    return CONFIG, PACS, RETRIEVE_CONFIG, SCHEDULE_CONFIG, conn, log_dir

# ─── PACS 선택 ──────────────────────────────────────────────────────────────
def select_pacs(CONFIG, PACS):
    if CONFIG.running_mode.lower() == "simulation":
        return PACS.research, PACS.simulation
    else:
        return PACS.research, PACS.clinical

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


def insert_findscus(conn, event) -> int:
    sql = """
    INSERT INTO findscus
      (ts, calling_aet, called_aet,
       peer_host, peer_port,
       query_retrieve_level,
       start_date, end_date,
       modalities_in_study,
       result_count, duration_ms,
       status, error_detail)
    VALUES (
      %s, %s, %s,
      %s, %s,
      %s,
      %s, %s,
      %s,
      %s, %s,
      %s, %s
    )
    RETURNING find_id
    """
    params = (
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
    )
    with conn.cursor() as cur:
        cur.execute(sql, params)
        find_id = cur.fetchone()[0]
    conn.commit()
    return find_id


def insert_movescus (conn, event):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO movescus
              (find_id, ts, calling_aet, called_aet, peer_host, peer_port, pending_count, duration_ms, status, error_detail, study_instance_uid)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event["find_id"],
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

def update_batch_status(conn, process_name: str, last_date: date):
    """
    batch_status 테이블의 last_processed_date와 updated_at을 갱신합니다.
    해당 process_name 이 없으면 INSERT, 있으면 UPDATE 합니다.
    """
    sql = """
    INSERT INTO batch_status (process_name, last_processed_date, updated_at)
    VALUES (%s, %s, NOW())
    ON CONFLICT (process_name) DO UPDATE
      SET last_processed_date = EXCLUDED.last_processed_date,
          updated_at          = EXCLUDED.updated_at
    """
    with conn.cursor() as cur:
        cur.execute(sql, (process_name, last_date))
    conn.commit()


def run_retrieve():

    batch_success = 1

    # 1) 환경 초기화
    CONFIG, PACS, RETRIEVE_CONFIG, SCHEDULE_CONFIG, conn, log_dir = init_environment()
    print(f"▶ Running mode: {CONFIG.running_mode}")
    source, target = select_pacs(CONFIG, PACS)

    print(target)
    date_range     = make_batch_date_range()
    modalities     = RETRIEVE_CONFIG.clinical_to_research.modalities

    all_uids = []
    # 2) C-FIND (모달리티별)
    for modality in modalities:
        print(f"\n=== Modality: {modality} ===")

        cmd = [
            "findscu", "-v", "-S",
            "-aet", source.aet, "-aec", target.aet,
            target.ip, str(target.port),
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

        save_logs(log_dir, "findscu", modality, ts_start, std_combined_text, "no_uid")

        # UID 추출
        uids = re.findall(r'\(0020,000d\) UI \[([^\]]+)\]', std_combined_text)
        print(f"  Found {len(uids)} UIDs")
        all_uids.extend(uids)

        # C-FIND 이벤트 DB 기록
        event_find = {
            "ts": ts_start,
            "calling_aet": source.aet,
            "called_aet": target.aet,
            "peer_host": target.ip,
            "peer_port": target.port,
            "query_retrieve_level": "STUDY",
            "start_date": parse_start_date(date_range),
            "end_date":   parse_end_date(date_range),
            "modalities_in_study": modality,
            "result_count": len(uids),
            "duration_ms": duration_ms,
            "status": status,
            "error_detail": std_combined_text.strip() or None,
        }
        sanitize_event(event_find)
        find_id = insert_findscus(conn, event_find)

        # 3) 이 모달리티에서 나온 UID만 바로 MOVE 처리
        unique_uids = list(dict.fromkeys(uids))
        for uid in unique_uids:
            clean_uid = uid.replace("\x00", "")
            move_cmd = [
                "movescu", "-v",
                "-aet", source.aet, "-aec", target.aet,
                target.ip, str(target.port),
                "-k", "QueryRetrieveLevel=STUDY",
                "-k", f"StudyInstanceUID={clean_uid}"
            ]
            print("▶ C-MOVE:", " ".join(move_cmd))

            ts_mv_start = datetime.now()
            mv_std_combined_text, mv_status = run_process(move_cmd)
            ts_mv_end = datetime.now()
            mv_duration = int((ts_mv_end - ts_mv_start).total_seconds() * 1000)

            save_logs(log_dir, "movescu", modality, ts_mv_start, mv_std_combined_text, clean_uid)
            pending_count = mv_std_combined_text.lower().count("pending")

            event_move = {
                "find_id": find_id,
                "ts": ts_mv_start,
                "calling_aet": source.aet,
                "called_aet":  target.aet,
                "peer_host":   target.ip,
                "peer_port":   target.port,
                "pending_count": pending_count,
                "duration_ms": mv_duration,
                "status": mv_status,
                "error_detail": mv_std_combined_text.strip() or None,
                "study_instance_uid": clean_uid,
            }
            sanitize_event(event_move)
            insert_movescus(conn, event_move)

            batch_success = batch_success * (1 if status == "SUCCESS" and mv_status == "SUCCESS" else 0)

    



    if batch_success == 1:
        # date_range 가 "YYYYMMDD-YYYYMMDD" 이므로 끝 날짜를 꺼내서 저장
        last_date = parse_end_date(date_range)
        update_batch_status(conn, "findscu", last_date)
        print(f"▶ Batch 전체 성공: last_processed_date → {last_date}")
    else:
        print("⚠️ Batch 중 일부 실패 발생: batch_status 갱신 생략")
     

    # 4) 모든 모달리티 처리 후에야 커넥션을 닫습니다.
    conn.close()    

if __name__ == "__main__":
    run_retrieve()

