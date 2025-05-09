#!/usr/bin/env python3
"""
scripts/init_db.py

– config/database.yaml 에서 DB 접속 정보 로드
– config/schema_rpacs.yaml 에서 테이블 정의 로드
– rpacs_admin(슈퍼유저)로 rpacs, nmdose 데이터베이스가 없으면 생성
– nmuser(애플리케이션 계정)로 RPACS 스키마 테이블이 없으면 생성
– alembic 폴더가 있으면 마이그레이션 적용
"""

import subprocess
import yaml
import psycopg2
from pathlib import Path
from nmdose.config_loader.database import get_db_config  # 설정 로더에서 가져오기

def ensure_database(name: str, admin_cfg):
    """
    rpacs_admin 슈퍼유저로 'postgres' DB에 접속해
    name 데이터베이스가 없으면 생성합니다.
    """
    conn = psycopg2.connect(
        dbname=admin_cfg.database,
        host=admin_cfg.host,
        port=admin_cfg.port,
        user=admin_cfg.user,
        password=admin_cfg.user
    )
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,))
        if not cur.fetchone():
            print(f"▶ Creating database '{name}' as superuser...")
            cur.execute(f'CREATE DATABASE "{name}";')
            print(f"   ✓ Database '{name}' created.")
        else:
            print(f"▶ Database '{name}' already exists.")
    conn.close()

def ensure_tables(app_cfg, tables: dict):
    """
    nmuser 애플리케이션 계정으로 지정된 데이터베이스에 접속해,
    tables 정의에 따라 없으면 CREATE TABLE IF NOT EXISTS 로 테이블을 생성합니다.
    """
    conn = psycopg2.connect(
        dbname=app_cfg.database,
        host=app_cfg.host,
        port=app_cfg.port,
        user=app_cfg.user,
        password=app_cfg.user
    )
    with conn:
        with conn.cursor() as cur:
            for tbl_name, tbl_def in tables.items():
                cols = []
                for col in tbl_def["columns"]:
                    line = f"{col['name']} {col['type']}"
                    if col.get("primary_key"):
                        line += " PRIMARY KEY"
                    cols.append(line)
                ddl = (
                    f"CREATE TABLE IF NOT EXISTS {tbl_name} (\n"
                    "  " + ",\n  ".join(cols) + "\n);"
                )
                print(f"▶ Ensuring table '{tbl_name}' as nmuser...")
                cur.execute(ddl)
                print(f"   ✓ Table '{tbl_name}' OK.")
    conn.close()

def main():
    # 1) DB 설정 로드
    dbs        = get_db_config()
    admin_cfg  = dbs.rpacs_admin   # 슈퍼유저 정보
    rpacs_cfg  = dbs.rpacs         # nmuser RPACS용
    nmdose_cfg = dbs.nmdose        # nmuser NMDOSE용

    # 2) 스키마 정의 로드
    schema_file = Path(__file__).parent.parent / "config" / "schema_rpacs.yaml"
    if not schema_file.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    schema_data = yaml.safe_load(schema_file.read_text(encoding="utf-8-sig"))

    # 3) 데이터베이스 생성 (슈퍼유저)
    for dbname in (rpacs_cfg.database, nmdose_cfg.database):
        ensure_database(dbname, admin_cfg)

    # 4) RPACS 스키마 테이블 생성 (nmuser)
    ensure_tables(rpacs_cfg, schema_data["tables"])

    # 5) Alembic 마이그레이션 적용 (선택)
    alembic_dir = Path(__file__).parent.parent / "alembic"
    if alembic_dir.is_dir():
        print("▶ Applying Alembic migrations…")
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("   ✓ Alembic migrations applied.")
    else:
        print("▶ No 'alembic' directory found, skipping migrations.")

if __name__ == "__main__":
    main()
