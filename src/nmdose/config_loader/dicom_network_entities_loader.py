# src/nmdose/config_loader/dicom_network_entities_loader.py

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


@dataclass(frozen=True)
class DicomNetworkEntities:
    clinical: DicomEndpoint
    simulation: DicomEndpoint
    research: DicomEndpoint
    dose: DicomEndpoint


# 모듈 수준 캐시
_dicom_entities_cache: DicomNetworkEntities | None = None


def get_dicom_network_entities_config(base_path: str = None) -> DicomNetworkEntities:
    """
    config/dicom_network_entities.yaml 파일을 읽어 DicomNetworkEntities 객체로 반환합니다.
    """
    global _dicom_entities_cache
    if _dicom_entities_cache is None:
        cfg_dir = Path(base_path) if base_path else Path(__file__).parents[3] / "config"
        cfg_file = cfg_dir / "dicom_network_entities.yaml"

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
                    port=int(info["port"])
                )

            _dicom_entities_cache = DicomNetworkEntities(
                clinical=_endpoint("clinicalPACS"),
                simulation=_endpoint("simulationPACS"),
                research=_endpoint("researchPACS"),
                dose=_endpoint("dosePACS")
            )
            log.info("DICOM 네트워크 설정 로드 완료")

        except KeyError as e:
            log.error(f"dicom_network_entities.yaml에 필수 설정이 없습니다: {e}")
            raise KeyError(f"dicom_network_entities.yaml에 필수 설정이 없습니다: {e}")
        except (TypeError, ValueError) as e:
            log.error(f"dicom_network_entities.yaml 값 형식 오류: {e}")
            raise ValueError(f"dicom_network_entities.yaml 값 형식 오류: {e}")

    return _dicom_entities_cache
