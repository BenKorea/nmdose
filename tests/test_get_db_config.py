# tests/test_db_config.py

import pytest
from pathlib import Path
from nmdose.config_loader import get_db_config

@pytest.fixture
def sample_db_config(tmp_path, monkeypatch):
    # 1) 임시 config.yaml 생성: 실제 rpacs 기본값 반영
    content = """
database:
  rpacs:
    database: rpacs
    user: nmuser
    host: 127.0.0.1
    port: 5432
"""
    CONFIG_path = tmp_path / "config.yaml"
    CONFIG_path.write_text(content, encoding="utf-8")

    # 2) loader가 이 파일을 읽도록 환경변수 설정
    monkeypatch.setenv("NMDOSE_CONFIG", str(CONFIG_path))

    return CONFIG_path

def test_get_db_config_defaults(sample_db_config):
    db = get_db_config().rpacs
    # 실제 rpacs 기본 설정값 검증
    assert db.database == "rpacs"
    assert db.user     == "nmuser"
    assert db.host     == "127.0.0.1"
    assert db.port     == 5432

