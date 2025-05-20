#!/usr/bin/env python3
"""
dicom_network_entities_loader.py

프로젝트 최상위의 config/dicom_network_entities.yaml 한 파일만 읽어 오는 설정 로더 모듈입니다.
"""

from pathlib import Path
import yaml
from dataclasses import dataclass

@dataclass(frozen=True)
class DicomEndpoint:
    """
    하나의 PACS 서버 접속 정보를 담는 데이터 클래스.
    Attributes:
      aet  (str): AE Title
      ip   (str): 호스트 주소
      port (int): 포트 번호
    """
    aet: str
    ip: str
    port: int

@dataclass(frozen=True)
class PACSConfig:
    """
    dicom_network_entities.yaml 에 정의된 모든 PACS 엔드포인트를 담는 데이터 클래스.
    Attributes:
      clinical   (DicomEndpoint): 임상용 PACS
      simulation (DicomEndpoint): 시뮬레이션용 PACS
      research   (DicomEndpoint): 리서치용 PACS
      dose       (DicomEndpoint): 선량 저장용 PACS
    """
    clinical: DicomEndpoint
    simulation: DicomEndpoint
    research: DicomEndpoint
    dose: DicomEndpoint

# 모듈 수준 캐시 (파일을 한 번만 읽도록)
_pacs_cache: PACSConfig | None = None

def get_pacs_config(base_path: str = None) -> PACSConfig:
    """
    프로젝트 루트/config/dicom_network_entities.yaml 파일을 읽어서 PACSConfig 객체로 반환합니다.
    반복 호출 시 캐시된 객체를 재사용합니다.

    Args:
      base_path (str, optional): dicom_network_entities.yaml 이 있는 디렉터리 경로.
                                 지정하지 않으면 이 파일 위치에서
                                 세 단계 상위(프로젝트 루트)로 올라가 config/ 폴더를 기본으로 사용합니다.

    Returns:
      PACSConfig: 읽어들인 PACS 엔드포인트 정보를 담은 불변 데이터 클래스 인스턴스.

    Raises:
      FileNotFoundError: dicom_network_entities.yaml 파일이 없을 때.
      KeyError: 필수 키가 누락되었을 때.
      ValueError: 값이 올바른 타입/포맷이 아닐 때.
    """
    global _pacs_cache
    if _pacs_cache is None:
        # 기본 경로 결정
        if base_path:
            cfg_dir = Path(base_path)
        else:
            # 이 파일(src/nmdose/config_loader/pacs.py)로부터
            # parents[0] = config_loader
            # parents[1] = nmdose
            # parents[2] = src
            # parents[3] = 프로젝트 루트
            cfg_dir = Path(__file__).parents[3] / "config"

        cfg_file = cfg_dir / "dicom_network_entities.yaml"
        if not cfg_file.is_file():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {cfg_file}")

        data = yaml.safe_load(cfg_file.read_text(encoding="utf-8-sig"))
        # 각 PACS 항목이 있는지 검증
        try:
            def _endpoint(key):
                info = data[key]
                aet = info["aet"]
                ip = info["ip"]
                port = int(info["port"])
                return DicomEndpoint(aet=aet, ip=ip, port=port)

            clinical   = _endpoint("clinicalPACS")
            simulation = _endpoint("simulationPACS")
            research   = _endpoint("researchPACS")
            dose       = _endpoint("dosePACS")
        except KeyError as e:
            raise KeyError(f"dicom_network_entities.yaml에 필수 설정이 없습니다: {e}")
        except (TypeError, ValueError) as e:
            raise ValueError(f"dicom_network_entities.yaml 값 형식 오류: {e}")

        _pacs_cache = PACSConfig(
            clinical=clinical,
            simulation=simulation,
            research=research,
            dose=dose
        )

    return _pacs_cache
