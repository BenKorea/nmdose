# tests/test_get_config.py

import pytest
import os
from pathlib import Path
from nmdose.config_loader import get_config

@pytest.fixture
def sample_config_file(tmp_path, monkeypatch):
    # 1) 임시 config.yaml 생성 (running_mode만 정의)
    content = """
running_mode: simulation
"""
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(content, encoding="utf-8")

    # 2) ENV 변수를 통해 loader가 이 파일을 읽도록 설정
    monkeypatch.setenv("NMDOSE_CONFIG", str(cfg_path))

    return cfg_path

def test_get_config_running_mode_only(sample_config_file):
    cfg = get_config()
    # running_mode 필드만 테스트
    assert cfg.running_mode.lower() == "simulation"
