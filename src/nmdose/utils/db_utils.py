#!/usr/bin/env python3
"""
db_utils.py

RPACS용 PostgreSQL에 `batch_status` 테이블이 없으면 생성하고,
주어진 날짜를 `last_processed_date`로 기록하는 유틸리티 함수들입니다.
"""

import psycopg2
from psycopg2 import sql
from datetime import date
from nmdose.config_loader.database import get_db_config

def _get_rpacs_connection():
    """RPACS 데이터베이스에 연결을 생성하여 반환합니다."""
    db_conf = get_db_config().rpacs
    # 비밀번호는 사용자명과 동일하다고 가정합니다. 필요 시 수정하세요.
    return psycopg2.connect(
        host=db_conf.host,
        port=db_conf.port,
        dbname=db_conf.database,
        user=db_conf.user,
        password=db_conf.user
    )

def ensure_batch_status_table():
    """
    'batch_status' 테이블이 없으면 생성합니다.
    스키마:
      process_name TEXT PRIMARY KEY,
      last_date    DATE    NOT NULL,
      updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    """
    conn = _get_rpacs_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS batch_status (
                        process_name TEXT PRIMARY KEY,
                        last_date    DATE    NOT NULL,
                        updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
                    );
                """)
    finally:
        conn.close()

def record_last_processed_date(process_name: str, last_date: date):
    """
    주어진 프로세스 이름과 날짜를 batch_status 테이블에 기록합니다.
    테이블이 없으면 먼저 생성합니다.

    Args:
      process_name (str): 배치 작업 고유 이름 (예: 'night_batch')
      last_date    (date): 처리 완료된 마지막 날짜
    """
    ensure_batch_status_table()
    conn = _get_rpacs_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO batch_status (process_name, last_date)
                    VALUES (%s, %s)
                    ON CONFLICT (process_name) DO UPDATE
                      SET last_date  = EXCLUDED.last_date,
                          updated_at = now();
                    """,
                    (process_name, last_date)
                )
    finally:
        conn.close()
