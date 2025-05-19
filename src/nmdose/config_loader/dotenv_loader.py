# src/nmdose/config_loader/dotenv_loader.py
from pathlib import Path
from dotenv import load_dotenv

def init_dotenv(env_path: Path | str = None):
    """
    프로젝트 루트의 .env 파일을 로드합니다.
    env_path 인자를 주면 그 경로를 우선 사용합니다.
    """
    if env_path is None:
        # 이 파일 위치에서 루트(3단계 상위)로 올라가 .env 찾기
        env_path = Path(__file__).parents[3] / ".env"
    load_dotenv(dotenv_path=env_path)
