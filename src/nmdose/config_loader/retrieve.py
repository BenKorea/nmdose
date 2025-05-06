#!/usr/bin/env python3
"""
retrieve.py

프로젝트 최상위의 config/retrieve.yaml 파일에서 리트리브 옵션을 읽어오는 설정 로더 모듈입니다.
"""

from pathlib import Path
import yaml
from dataclasses import dataclass

@dataclass(frozen=True)
class ClinicalToResearchConfig:
    """
    clinicalPACS → researchPACS 리트리브 옵션
    Attributes:
      modalities (list[str]): 허용할 modality 리스트 (e.g. ["NM", "PT"])
      exclude_if_study_description_contains (str): 해당 문자열 포함 시 제외할 study description 키워드
    """
    modalities: list[str]
    exclude_if_study_description_contains: str

@dataclass(frozen=True)
class CTDoseRetrievingConfig:
    """
    researchPACS → dosePACS CT 선량 리트리브 옵션
    Attributes:
      priority (str): 우선 시리즈 (예: "SR")
      fallback_series_description (list[str]): 우선 조건 미달 시 대체 시리즈 설명 리스트
      fallback_to_all_ct (bool): 위 조건 모두 없으면 모든 CT 시리즈 리트리브 여부
    """
    priority: str
    fallback_series_description: list[str]
    fallback_to_all_ct: bool

@dataclass(frozen=True)
class PetImageOptionCondition:
    """
    PET 리트리브 조건
    Attributes:
      modality (str): "PET"
      image_number (int): 리트리브할 ImageNumber 값
    """
    modality: str
    image_number: int

@dataclass(frozen=True)
class PetImageOption:
    """
    PET 리트리브 옵션 전체
    Attributes:
      enabled (bool): PET 옵션 사용 여부
      condition (PetImageOptionCondition): PET 조건 객체
    """
    enabled: bool
    condition: PetImageOptionCondition

@dataclass(frozen=True)
class ResearchToDoseConfig:
    """
    researchPACS → dosePACS 리트리브 옵션 전체
    Attributes:
      ct_dose_retrieving (CTDoseRetrievingConfig): CT 용 선량 옵션
      pet_image_option (PetImageOption): PET 용 이미지 옵션
    """
    ct_dose_retrieving: CTDoseRetrievingConfig
    pet_image_option: PetImageOption

@dataclass(frozen=True)
class RetrieveConfig:
    """
    retrieve.yaml 에 정의된 모든 리트리브 옵션
    Attributes:
      clinical_to_research (ClinicalToResearchConfig)
      research_to_dose (ResearchToDoseConfig)
    """
    clinical_to_research: ClinicalToResearchConfig
    research_to_dose: ResearchToDoseConfig

# 모듈 수준 캐시 (파일 I/O 최소화)
_retrieve_cache: RetrieveConfig | None = None

def get_retrieve_config(base_path: str = None) -> RetrieveConfig:
    """
    config/retrieve.yaml 파일을 읽어 RetrieveConfig 객체로 반환합니다.
    반복 호출 시 캐시된 객체를 재사용합니다.

    Args:
      base_path (str, optional): retrieve.yaml 이 있는 디렉터리 경로.
                                 지정하지 않으면 이 파일 위치에서 세 단계 상위(프로젝트 루트)로 올라가 config/ 폴더를 기본으로 사용합니다.

    Returns:
      RetrieveConfig: 읽어들인 리트리브 옵션을 담은 불변 데이터 클래스 인스턴스.

    Raises:
      FileNotFoundError: retrieve.yaml 파일이 없을 때.
      KeyError: 필수 키가 누락되었을 때.
      ValueError: 값이 올바른 타입/포맷이 아닐 때.
    """
    global _retrieve_cache
    if _retrieve_cache is None:
        # 기본 config 폴더 위치 결정
        if base_path:
            cfg_dir = Path(base_path)
        else:
            # 이 파일(src/nmdose/config_loader/retrieve.py)로부터
            # parents[0]=config_loader, parents[1]=nmdose, parents[2]=src, parents[3]=프로젝트 루트
            cfg_dir = Path(__file__).parents[3] / "config"

        cfg_file = cfg_dir / "retrieve.yaml"
        if not cfg_file.is_file():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {cfg_file}")

        data = yaml.safe_load(cfg_file.read_text(encoding="utf-8-sig"))

        # clinical_to_research 파싱
        ctr = data["clinical_to_research"]
        clinical_cfg = ClinicalToResearchConfig(
            modalities=ctr["modalities"],
            exclude_if_study_description_contains=ctr["exclude_if_study_description_contains"]
        )

        # research_to_dose 파싱
        r2d = data["research_to_dose"]
        ct = r2d["ct_dose_retrieving"]
        ct_cfg = CTDoseRetrievingConfig(
            priority=ct["priority"],
            fallback_series_description=ct["fallback_series_description"],
            fallback_to_all_ct=ct["fallback_to_all_ct"]
        )
        pet = r2d["pet_image_option"]
        pet_cond = pet["condition"]
        pet_cfg = PetImageOption(
            enabled=pet["enabled"],
            condition=PetImageOptionCondition(
                modality=pet_cond["modality"],
                image_number=pet_cond["image_number"]
            )
        )
        research_cfg = ResearchToDoseConfig(
            ct_dose_retrieving=ct_cfg,
            pet_image_option=pet_cfg
        )

        _retrieve_cache = RetrieveConfig(
            clinical_to_research=clinical_cfg,
            research_to_dose=research_cfg
        )

    return _retrieve_cache
