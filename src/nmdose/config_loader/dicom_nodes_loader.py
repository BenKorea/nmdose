#!/usr/bin/env python3
"""
dicom_nodes_loader.py

프로젝트 최상위의 config/dicom_nodes.yaml 한 파일만 읽어 오는 설정 로더 모듈입니다.
"""

# ───── 표준 라이브러리 ─────
from pathlib import Path
from dataclasses import dataclass
import logging

# ───── 서드파티 라이브러리 ─────
import yaml

# ───── 로거 객체 생성 ─────
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DicomEndpoint:
    aet: str
    ip: str
    port: int
    enable_tls: bool = False
    cert_file: str | None = None
    key_file: str | None = None


@dataclass(frozen=True)
class DicomNodes:
    clinical: DicomEndpoint
    simulation: DicomEndpoint
    research: DicomEndpoint
    dose: DicomEndpoint


# 모듈 수준 캐시
_dicom_nodes_cache: DicomNodes | None = None

def get_nodes_config(base_path: str = None) -> DicomNodes:
    """
    config/dicom_nodes.yaml 파일을 읽어 DicomNodes 객체로 반환합니다.
    """
    global _dicom_nodes_cache
    if _dicom_nodes_cache is None:
        cfg_dir = Path(base_path) if base_path else Path(__file__).parents[3] / "config"
        cfg_file = cfg_dir / "dicom_nodes.yaml"

        if not cfg_file.is_file():
            log.error(f"설정 파일을 찾을 수 없습니다: {cfg_file}")
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {cfg_file}")

        data = yaml.safe_load(cfg_file.read_text(encoding="utf-8-sig"))

        try:
            def _endpoint(key):
                info = data[key]
                return DicomEndpoint(
                    aet=info["aet"],
                    ip=info["ip"],
                    port=int(info["port"]),
                    enable_tls=info.get("enable_tls", False),
                    cert_file=info.get("cert_file"),
                    key_file=info.get("key_file"),
                )

            _dicom_nodes_cache = DicomNodes(
                clinical=_endpoint("clinicalPACS"),
                simulation=_endpoint("simulationPACS"),
                research=_endpoint("researchPACS"),
                dose=_endpoint("dosePACS")
            )
            log.info("DICOM 노드 설정 로드 완료")

        except KeyError as e:
            log.error(f"dicom_nodes.yaml에 필수 설정이 없습니다: {e}")
            raise KeyError(f"dicom_nodes.yaml에 필수 설정이 없습니다: {e}")
        except (TypeError, ValueError) as e:
            log.error(f"dicom_nodes.yaml 값 형식 오류: {e}")
            raise ValueError(f"dicom_nodes.yaml 값 형식 오류: {e}")

    return _dicom_nodes_cache
