# src/nmdose/utils/date_utils.py

# ───── 표준 라이브러리 ─────
from datetime import datetime, date, timedelta
import logging

# ───── 서드파티 라이브러리 ─────
from dateutil import parser
import psycopg2

# ───── 내부 모듈 ─────
from nmdose.config_loader.retrieve_options_loader import get_retrieve_config
from nmdose.config_loader.database import get_db_config

# ───── 로거 객체 생성 ─────
log = logging.getLogger(__name__)


def make_batch_date_range() -> str:
    """
    retrieve_options.retrieve_to_research.* 설정을 기반으로 날짜 범위를 계산합니다.
    DB의 마지막 처리일이 있으면 이를 기준으로 시작일을 정하며,
    일일 시작일을 넘지 않도록 종료일을 제한합니다.
    반환값: 'YYYYMMDD-YYYYMMDD' 문자열
    """
    RETRIEVE_OPTIONS = get_retrieve_config()
    cfg = RETRIEVE_OPTIONS.retrieve_to_research

    # 설정값 파싱
    start_str       = cfg.batch_start_date      # 예: "20240222"
    batch_days      = cfg.batch_days            # 예: 7
    daily_start_str = cfg.daily_start_date      # 예: "20250508"

    # 문자열 → 날짜 객체
    start_dt       = parser.parse(start_str).date()
    daily_start_dt = parser.parse(daily_start_str).date()

    # DB에서 마지막 처리일 조회
    db_conf = get_db_config().rpacs
    conn = psycopg2.connect(
        host=db_conf.host,
        port=db_conf.port,
        user=db_conf.user,
        password=db_conf.user,
        dbname=db_conf.database
    )
    with conn, conn.cursor() as cur:
        cur.execute("""
            SELECT last_processed_date
              FROM batch_status
             ORDER BY last_processed_date DESC
             LIMIT 1
        """)
        row = cur.fetchone()

    last_processed_dt = None
    if row and row[0]:
        raw = row[0]
        last_processed_dt = raw if isinstance(raw, date) else parser.parse(str(raw)).date()

    # 시작일 결정
    effective_start = (
        last_processed_dt if last_processed_dt and last_processed_dt >= start_dt else start_dt
    )

    # 종료일 계산
    candidate_end = effective_start + timedelta(days=batch_days - 1)
    effective_end = min(candidate_end, daily_start_dt)

    # 포맷 변환
    start_fmt = effective_start.strftime("%Y%m%d")
    end_fmt   = effective_end.strftime("%Y%m%d")

    return f"{start_fmt}-{end_fmt}"


def parse_start_date(range_str: str) -> date:
    """'YYYYMMDD-YYYYMMDD' 형식에서 시작일 추출"""
    return datetime.strptime(range_str.split("-", 1)[0], "%Y%m%d").date()


def parse_end_date(range_str: str) -> date:
    """'YYYYMMDD-YYYYMMDD' 형식에서 종료일 추출"""
    return datetime.strptime(range_str.split("-", 1)[1], "%Y%m%d").date()
