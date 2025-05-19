#!/usr/bin/env python3
"""
scripts/init_db.py

– config/database.yaml 에서 DB 접속 정보 로드
– config/database_schema.yaml 에서 스키마 및 테이블 정의 로드
– rpacs_admin(슈퍼유저)로 통합 DB가 없으면 생성
– nmuser(애플리케이션 계정)로 사용자 없으면 생성
– 통합 DB에 두 스키마(rpacs, dosepacs)가 없으면 생성
– nmuser로 각 스키마에 권한 부여
– nmuser로 각 스키마별 테이블 생성
– alembic 폴더가 있으면 마이그레이션 적용
"""

import subprocess
import yaml
import psycopg2
from pathlib import Path
from nmdose.config_loader.database import get_db_config


def ensure_user(username: str, admin_cfg):
    """
    postgres 슈퍼유저로 접속해 사용자 계정(username)이 없으면 생성합니다.
    비밀번호는 username과 동일하게 설정됩니다.
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
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (username,))
        if not cur.fetchone():
            print(f"▶ Creating user '{username}'...")
            cur.execute(f"CREATE USER {username} WITH PASSWORD %s;", (username,))
            print(f"   ✓ User '{username}' created.")
        else:
            print(f"▶ User '{username}' already exists.")
    conn.close()


def ensure_database(name: str, admin_cfg):
    """
    rpacs_admin 슈퍼유저로 접속해
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


def grant_schema_privileges_on_all(admin_cfg, username: str, db_names: list[str], schema: str):
    """
    모든 대상 DB의 {schema} 스키마에 대해 CREATE, USAGE 권한을 부여합니다.
    """
    for dbname in db_names:
        conn = psycopg2.connect(
            dbname=dbname,
            host=admin_cfg.host,
            port=admin_cfg.port,
            user=admin_cfg.user,
            password=admin_cfg.user
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            print(f"▶ Granting CREATE, USAGE ON SCHEMA {schema} TO {username} in DB '{dbname}'...")
            cur.execute(f"GRANT CREATE, USAGE ON SCHEMA {schema} TO {username};")
            print(f"   ✓ Granted in '{dbname}'.")
        conn.close()


def ensure_tables(app_cfg, tables: dict, schema: str):
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
                fq = f"{schema}.{tbl_name}"
                ddl = (
                    f"CREATE TABLE IF NOT EXISTS {fq} (\n"
                    "  " + ",\n  ".join(cols) + "\n);"
                )
                print(f"▶ Ensuring table '{fq}' as {app_cfg.user}...")
                cur.execute(ddl)
                print(f"   ✓ Table '{fq}' OK.")
    conn.close()


def main():
    # 1) DB 설정 로드
    dbs       = get_db_config()
    admin_cfg = dbs.rpacs_admin   # 슈퍼유저 정보
    rpacs_cfg = dbs.rpacs         # nmuser, 통합 DB용

    # 1.5) 사용자 계정 생성
    ensure_user(rpacs_cfg.user, admin_cfg)

    # 1.6) 데이터베이스 생성
    ensure_database(rpacs_cfg.database, admin_cfg)

    # 2) 스키마 정의 로드
    schema_file = Path(__file__).parent.parent / "config" / "database_schema.yaml"
    if not schema_file.is_file():
        raise FileNotFoundError(f"Schema file not found: {schema_file}")
    data    = yaml.safe_load(schema_file.read_text(encoding="utf-8-sig"))
    schemas = data["schema"]

    # 3) 스키마 생성
    for schema_name in schemas:
        conn = psycopg2.connect(
            dbname=rpacs_cfg.database,
            host=admin_cfg.host,
            port=admin_cfg.port,
            user=admin_cfg.user,
            password=admin_cfg.user
        )
        conn.autocommit = True
        with conn.cursor() as cur:
            print(f"▶ Creating schema '{schema_name}' if not exists...")
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name} AUTHORIZATION {rpacs_cfg.user};")
            print(f"   ✓ Schema '{schema_name}' OK.")
        conn.close()

    # 4) 스키마별 권한 부여
    for schema_name in schemas:
        grant_schema_privileges_on_all(
            admin_cfg,
            rpacs_cfg.user,
            [rpacs_cfg.database],
            schema=schema_name
        )

    # 5) 스키마별 테이블 생성
    for schema_name, defn in schemas.items():
        ensure_tables(rpacs_cfg, defn["tables"], schema=schema_name)

    # 6) Alembic 마이그레이션 적용 (선택)
    alembic_dir = Path(__file__).parent.parent / "alembic"
    if alembic_dir.is_dir():
        print("▶ Applying Alembic migrations…")
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("   ✓ Alembic migrations applied.")
    else:
        print("▶ No 'alembic' directory found, skipping migrations.")


if __name__ == "__main__":
    main()
