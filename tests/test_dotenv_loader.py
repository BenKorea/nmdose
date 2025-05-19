import os
from pathlib import Path
import pytest

from nmdose.config_loader.dotenv_loader import init_dotenv

def test_init_dotenv_loads_values(tmp_path, monkeypatch):
    # 1) 임시 .env 파일 생성
    env_file = tmp_path / ".env"
    env_file.write_text("RUNNING_MODE=simulation\nOTHER_VAR=hello\n")

    # 2) 테스트 중 기존 환경변수 격리
    #    monkeypatch.delenv 으로 같은 키가 있으면 제거
    monkeypatch.delenv("RUNNING_MODE", raising=False)
    monkeypatch.delenv("OTHER_VAR", raising=False)

    # 3) init_dotenv 호출 (env_path 인자에 임시 파일 경로 전달)
    init_dotenv(env_path=str(env_file))

    # 4) os.environ 에서 로드된 값 확인
    assert os.getenv("RUNNING_MODE") == "simulation"
    assert os.getenv("OTHER_VAR") == "hello"
