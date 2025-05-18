# src/nmdose/utils/date_utils.py

from datetime import datetime, date, timedelta
from dateutil import parser
import psycopg2
from nmdose import get_schedule_config, get_db_config

def make_batch_date_range() -> str:
    """
    schedule.batch_retrieving.start_date를 기준으로
    schedule.batch_retrieving.batch_days만큼 더한 종료 날짜를 계산하고,
    데이터베이스의 last_processed_date가 존재하면 이를 시작일로 사용하며,
    daily_retrieving.start_date를 넘지 않도록 보정한
    'YYYYMMDD-YYYYMMDD' 형태의 문자열을 반환한다.
    """
    # 1) 설정에서 시작일, 배치 일수, daily start 읽기
    sched            = get_schedule_config()
    start_str        = sched.batch_retrieving.start_date   # e.g. "20240222"
    batch_days       = sched.batch_retrieving.batch_days   # 예: 7
    daily_start_str  = sched.daily_retrieving.start_date   # e.g. "20250508"

    # 2) 문자열 → date
    start_dt        = parser.parse(start_str).date()
    daily_start_dt  = parser.parse(daily_start_str).date()

    # 3) DB에서 마지막 처리일 조회
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
        if isinstance(raw, date):
            last_processed_dt = raw
        else:
            last_processed_dt = parser.parse(str(raw)).date()

    # 4) effective_start 결정
    effective_start = (
        last_processed_dt
        if last_processed_dt and last_processed_dt >= start_dt
        else start_dt
    )

    # 5) batch_days 만큼 더한 후보 종료일
    candidate_end = effective_start + timedelta(days=batch_days - 1)

    # 6) 유효 종료일: daily_start_dt보다 늦으면 daily_start_dt, 아니면 candidate_end
    effective_end = (
        daily_start_dt
        if candidate_end >= daily_start_dt
        else candidate_end
    )

    # 7) 포맷팅
    start_fmt = effective_start.strftime("%Y%m%d")
    end_fmt   = effective_end.strftime("%Y%m%d")

    return f"{start_fmt}-{end_fmt}"

def parse_start_date(range_str: str) -> date:
    """
    "YYYYMMDD-YYYYMMDD" 형식의 문자열에서
    앞 8자리를 파싱하여 date 객체로 반환합니다.
    """
    # 1) 하이픈(-) 기준으로 나누기
    start_str = range_str.split("-", 1)[0]
    # 2) 문자열을 date 로 변환
    return datetime.strptime(start_str, "%Y%m%d").date()


def parse_end_date(range_str: str) -> date:
    """
    "YYYYMMDD-YYYYMMDD" 형식의 문자열에서
    뒤 8자리를 파싱하여 date 객체로 반환합니다.
    """
    # 1) 하이픈 이후 문자열
    #    split 대신 슬라이싱(range_str[-8:])을 써도 무방합니다.
    end_str = range_str.split("-", 1)[1]
    # 2) 문자열을 date 로 변환
    return datetime.strptime(end_str, "%Y%m%d").date()

