# File: src/nmdose/env/init.py
from pathlib import Path
import psycopg2

from nmdose import (
    get_config,
    get_pacs_config,
    get_retrieve_config,
    get_schedule_config,
    get_db_config,
    make_batch_date_range,
)


def init_environment():
    """
    설정 파일을 로드하고, PACS 엔드포인트, 조회 파라미터, DB 커넥션 및 로그 디렉터리를 초기화합니다.

    반환:
      CONFIG: 전체 설정
      calling: C-FIND 요청 SCU AET/IP/Port
      called: C-FIND 대상 PACS AET/IP/Port
      modalities: 조회할 modality 리스트
      date_range: StudyDate 범위 문자열
      conn: psycopg2 DB 커넥션
      log_dir: 로그 파일을 저장할 디렉터리 경로
    """
    # 기본 설정 로드
    CONFIG     = get_config()
    pacs    = get_pacs_config()
    rcfg    = get_retrieve_config()
    sched   = get_schedule_config()
    db_conf = get_db_config().rpacs

    # 실행 모드 출력
    print(f"▶ Running mode: {CONFIG.running_mode}")

    # PACS 엔드포인트 선택
    if CONFIG.running_mode.lower() == "simulation":
        calling, called = pacs.research, pacs.simulation
    else:
        calling, called = pacs.research, pacs.clinical
    print(f"▶ calling AET: {calling.aet}, IP: {calling.ip}, Port: {calling.port}")
    print(f"▶ called AET: {called.aet}, IP: {called.ip}, Port: {called.port}")

    # 조회할 modalities, 날짜 범위
    modalities = rcfg.clinical_to_research.modalities
    date_range = make_batch_date_range()
    print(f"▶ Modalities to query: {modalities}")
    print(f"▶ StudyDate range: {date_range}")

    # DB 연결
    conn = psycopg2.connect(
        dbname=db_conf.database,
        user=db_conf.user,
        password=db_conf.user,
        host=db_conf.host,
        port=db_conf.port
    )
    print(f"▶ Connected to DB: {db_conf.host}:{db_conf.port}/{db_conf.database}")

    # 로그 디렉터리 생성
    log_dir = Path(r"C:\nmdose\logs\batch")
    log_dir.mkdir(parents=True, exist_ok=True)
    print(f"▶ Log directory: {log_dir}")

    return CONFIG, calling, called, modalities, date_range, conn, log_dir
