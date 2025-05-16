#!/usr/bin/env python3
"""
config_loader.py

최소한의 기능으로 프로젝트 최상위의 config/config.yaml 한 파일만 읽어 오는 단순화된 설정 로더 모듈입니다.
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
      debug_mode   (bool): 디버그 모드 활성화 여부
    """
    running_mode: str
    debug_mode: bool

# 모듈 수준 캐시 (파일을 한 번만 읽도록)
_config_cache: Config | None = None

def get_config(base_path: str = None) -> Config:
    """
    프로젝트 루트/config/config.yaml 파일을 읽어서 Config 객체로 반환합니다.
    반복 호출 시 캐시된 객체를 재사용합니다.

    Args:
      base_path (str, optional): config.yaml 이 있는 디렉터리 경로.
                                 지정하지 않으면 이 파일 위치에서
                                 세 단계 상위(프로젝트 루트)로 올라가 config/ 폴더를 기본으로 사용합니다.

    Returns:
      Config: 읽어들인 설정을 담은 불변 데이터 클래스 인스턴스.

    Raises:
      FileNotFoundError: config.yaml 파일이 없을 때.
      KeyError: 필수 키가 누락되었을 때.
      ValueError: 값이 올바른 타입/포맷이 아닐 때.
    """
    global _config_cache
    if _config_cache is None:
        if base_path:
            cfg_dir = Path(base_path)
        else:
            # 이 파일(src/nmdose/config_loader/config_loader.py)로부터
            # parents[0] = config_loader
            # parents[1] = nmdose
            # parents[2] = src
            # parents[3] = 프로젝트 루트
            cfg_dir = Path(__file__).parents[3] / "config"

        cfg_file = cfg_dir / "config.yaml"

        if not cfg_file.is_file():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {cfg_file}")
        data = yaml.safe_load(cfg_file.read_text(encoding="utf-8-sig"))

        # 필수 키 검증
        try:
            running_mode = data["running_mode"]
            debug_mode   = data["debug_mode"]
        except KeyError as e:
            raise KeyError(f"config.yaml에 필수 설정이 없습니다: {e}")

        # 타입 검증
        if not isinstance(running_mode, str):
            raise ValueError(f"running_mode는 문자열이어야 합니다: {running_mode!r}")
        if not isinstance(debug_mode, bool):
            raise ValueError(f"debug_mode는 불리언이어야 합니다: {debug_mode!r}")

        _config_cache = Config(running_mode=running_mode, debug_mode=debug_mode)

    return _config_cache
