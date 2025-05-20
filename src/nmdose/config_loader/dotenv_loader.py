# src/nmdose/config_loader/dotenv_loader.py

# ───── 표준 라이브러리 ─────
from pathlib import Path
import logging
import os

# ───── 서드파티 라이브러리 ─────
from dotenv import load_dotenv

# ───── 로거 설정 ─────
log = logging.getLogger(__name__)
log.debug(f"▶ 로거 설정: {log.name} "
          f"(raw level={log.level}, effective={logging.getLevelName(log.getEffectiveLevel())})")

def init_dotenv(env_path: Path | str = None):
    """
    프로젝트 루트의 .env 파일을 로드합니다.
    env_path 인자를 주면 해당 경로를 우선 사용합니다.
    """
    if env_path is None:
        # 이 파일에서 세 단계 위가 프로젝트 루트
        env_path = Path(__file__).parents[3] / ".env"

    if not Path(env_path).is_file():
        log.info(f".env 파일이 없는 clinical mode로 정상적으로 시작됨: {env_path}")
        return

    load_dotenv(dotenv_path=env_path)
    log.info(f".env 파일이 있는 개발모드로 시작됨: {env_path}")

    # RUNNING_MODE 값 확인
    running_mode = os.getenv("RUNNING_MODE")
    if running_mode not in {"0", "1"}:
        log.error(f"❌ RUNNING_MODE 값이 잘못되었습니다: '{running_mode}' (0 또는 1이어야 함)")
        raise ValueError("RUNNING_MODE 값은 '0'(clinical) 또는 '1'(simulation)이어야 합니다.")
    else:
        mode_str = "simulation" if running_mode == "1" else "clinical"
        log.info(f"▶ RUNNING_MODE 값 확인됨: {running_mode} ({mode_str})")

