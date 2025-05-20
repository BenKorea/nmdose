# src/nmdose/env/init.py

# ───── 표준 라이브러리 ─────
import os
from pathlib import Path
import logging

# ───── 내부 모듈 ─────
from nmdose.config_loader.dotenv_loader import init_dotenv
from nmdose.config_loader.retrieve_options_loader import get_retrieve_options_config
from nmdose.config_loader.dicom_network_entities_loader import get_dicom_network_entities_config
from nmdose.utils.date_utils import make_batch_date_range

# ───── 로거 객체 생성 ─────
log = logging.getLogger(__name__)


def init_environment():
    """
    설정 파일을 로드하고, PACS 엔드포인트, 조회 파라미터 및 로그 디렉터리를 초기화합니다.

    반환:
      calling: C-FIND 요청 SCU AET/IP/Port
      called: C-FIND 대상 PACS AET/IP/Port
      modalities: 조회할 modality 리스트
      date_range: StudyDate 범위 문자열
      log_dir: 로그 파일을 저장할 디렉터리 경로
    """
    # .env 파일부터 로드 (환경변수 우선)
    init_dotenv()

    # PACS 및 retrieve 설정 로드
    PACS             = get_dicom_network_entities_config()
    RETRIEVE_OPTIONS = get_retrieve_options_config()

    # PACS 엔드포인트 선택 (RUNNING_MODE env var 기반)
    rm = os.getenv("RUNNING_MODE")
    log.info(f"▶ ENV RUNNING_MODE = {rm}")
    if rm == "1":
        calling, called = PACS.research, PACS.simulation
    else:
        calling, called = PACS.research, PACS.clinical

    # 조회할 modalities 및 날짜 범위
    modalities = RETRIEVE_OPTIONS.retrieve_to_research.modalities
    date_range = make_batch_date_range()
    log.info(f"조회할 Modalities: {modalities}")
    log.info(f"StudyDate 범위: {date_range}")

    # 로그 디렉터리 생성
    log_dir = Path(r"C:\nmdose\logs\batch")
    log_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Log 디렉터리 생성됨: {log_dir}")

    return calling, called, modalities, date_range, log_dir
