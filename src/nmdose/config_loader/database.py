#!/usr/bin/env python3
"""
database.py

프로젝트 최상위의 config/database.yaml 파일에서 데이터베이스 접속 정보를 읽어오는 설정 로더 모듈입니다.
"""

from pathlib import Path
import yaml
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class DBConfig:
    """
    하나의 데이터베이스 연결 정보를 담는 데이터 클래스.
    Attributes:
      database (str): 데이터베이스 이름
      user     (str): 사용자 이름
      host     (str): 호스트 주소
      port     (int): 포트 번호
    """
    database: str
    user: str
    host: str
    port: int

@dataclass(frozen=True)
class DatabaseSettings:
    """
    config/database.yaml에 정의된 DB 연결 정보를 담는 데이터 클래스.
    Attributes:
      rpacs_admin (DBConfig): RPACS 관리자용 DB (슈퍼유저)
      rpacs       (DBConfig): RPACS 애플리케이션용 DB (통합 DB)
    """
    rpacs_admin: DBConfig
    rpacs: DBConfig

# 모듈 수준 캐시 (파일 I/O 최소화)
_db_cache: Optional[DatabaseSettings] = None

def get_db_config(base_path: str = None) -> DatabaseSettings:
    """
    config/database.yaml 파일을 읽어 DatabaseSettings 객체로 반환합니다.
    반복 호출 시 캐시된 객체를 재사용합니다.

    Args:
      base_path (str, optional): database.yaml이 있는 디렉터리 경로.
                                 지정하지 않으면 이 파일 위치에서
                                 세 단계 상위(프로젝트 루트)로 올라가 config/ 폴더를 기본으로 사용합니다.

    Returns:
      DatabaseSettings: 읽어들인 DB 연결 정보를 담은 불변 데이터 클래스 인스턴스.

    Raises:
      FileNotFoundError: database.yaml 파일이 없을 때.
      KeyError: 필수 키가 누락되었을 때.
      ValueError: 값이 올바른 타입/포맷이 아닐 때.
    """
    global _db_cache
    if _db_cache is None:
        # config 폴더 경로 결정
        if base_path:
            cfg_dir = Path(base_path)
        else:
            cfg_dir = Path(__file__).parents[3] / "config"
        cfg_file = cfg_dir / "database.yaml"

        if not cfg_file.is_file():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {cfg_file}")

        data = yaml.safe_load(cfg_file.read_text(encoding="utf-8-sig"))

        # rpacs_admin 설정 파싱
        try:
            adm = data["rpacs_admin"]
            rpacs_admin_cfg = DBConfig(
                database=adm["database"],
                user=adm["user"],
                host=adm["host"],
                port=int(adm["port"])
            )
        except KeyError as e:
            raise KeyError(f"database.yaml의 'rpacs_admin' 설정이 잘못되었습니다: {e}")

        # rpacs(통합 DB) 애플리케이션 설정 파싱
        try:
            rp = data["rpacs"]
            rpacs_cfg = DBConfig(
                database=rp["database"],
                user=rp["user"],
                host=rp["host"],
                port=int(rp["port"])
            )
        except KeyError as e:
            raise KeyError(f"database.yaml의 'rpacs' 설정이 잘못되었습니다: {e}")

        _db_cache = DatabaseSettings(
            rpacs_admin=rpacs_admin_cfg,
            rpacs=rpacs_cfg
        )

    return _db_cache
