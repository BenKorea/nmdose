#!/usr/bin/env python3
"""
database_test.py

database.py 모듈의 get_db_config()를 호출하여
database.yaml에 정의된 DB 설정을 출력하는 간단한 테스트 스크립트입니다.
"""

from nmdose.config_loader.database import get_db_config

def main():
    # DatabaseSettings 객체를 얻어옵니다.
    dbs = get_db_config()

    # rpacs DB 설정 출력
    print("=== RPACS Database ===")
    print(f"Database: {dbs.rpacs.database}")
    print(f"User    : {dbs.rpacs.user}")
    print(f"Host    : {dbs.rpacs.host}")
    print(f"Port    : {dbs.rpacs.port}\n")

    # nmdose DB 설정 출력
    print("=== NMDOSE Database ===")
    print(f"Database: {dbs.nmdose.database}")
    print(f"User    : {dbs.nmdose.user}")
    print(f"Host    : {dbs.nmdose.host}")
    print(f"Port    : {dbs.nmdose.port}")

if __name__ == "__main__":
    main()
