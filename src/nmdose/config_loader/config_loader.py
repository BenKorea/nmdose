#!/usr/bin/env python3
"""
config_loader.py

프로젝트 최상위의 config/config.yaml 파일을 단순하게 읽어 오는 설정 로더.
"""

from pathlib import Path
import yaml
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    """
    config.yaml 에 정의된 값을 그대로 보관하는 데이터 클래스.

    Attributes:
      running_mode (str): "simulation" 또는 "clinical"
      logging_mode (str): "DEBUG", "INFO", "WARNING", "ERROR" 중 하나
    """
    running_mode: str
    logging_mode: str

_config_cache: Config | None = None

def get_config(base_path: str = None) -> Config:
    global _config_cache
    if _config_cache is None:
        if base_path:
            cfg_dir = Path(base_path)
        else:
            cfg_dir = Path(__file__).parents[3] / "config"

        cfg_file = cfg_dir / "config.yaml"

        if not cfg_file.is_file():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {cfg_file}")
        data = yaml.safe_load(cfg_file.read_text(encoding="utf-8-sig"))

        # 필수 키 검증
        try:
            running_mode = data["running_mode"]
            logging_mode = data["logging_mode"]
        except KeyError as e:
            raise KeyError(f"config.yaml에 필수 설정이 없습니다: {e}")

        # 타입 검증
        if not isinstance(running_mode, str):
            raise ValueError(f"running_mode는 문자열이어야 합니다: {running_mode!r}")
        if not isinstance(logging_mode, str):
            raise ValueError(f"logging_mode는 문자열이어야 합니다: {logging_mode!r}")

        _config_cache = Config(running_mode=running_mode, logging_mode=logging_mode)

    return _config_cache
