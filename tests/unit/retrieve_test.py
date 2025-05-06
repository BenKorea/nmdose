#!/usr/bin/env python3
"""
retrieve_test.py

retrieve.yaml 파일에서 로드된 리트리브 설정을 출력하는 테스트 스크립트입니다.
"""

from nmdose.config_loader.retrieve import get_retrieve_config

def main():
    # RetrieveConfig 객체를 얻어옵니다.
    rcfg = get_retrieve_config()

    # clinical → research 옵션 출력
    print("=== Clinical to Research ===")
    print("Modalities:", rcfg.clinical_to_research.modalities)
    print("Exclude if description contains:",
          rcfg.clinical_to_research.exclude_if_study_description_contains)

    # research → dose CT 옵션 출력
    print("\n=== Research to Dose (CT) ===")
    ct_cfg = rcfg.research_to_dose.ct_dose_retrieving
    print("Priority:", ct_cfg.priority)
    print("Fallback series descriptions:", ct_cfg.fallback_series_description)
    print("Fallback to all CT:", ct_cfg.fallback_to_all_ct)

    # PET 옵션 출력
    print("\n=== PET Image Option ===")
    pet_cfg = rcfg.research_to_dose.pet_image_option
    print("Enabled :", pet_cfg.enabled)
    print("Condition:", pet_cfg.condition.modality,
          "ImageNumber =", pet_cfg.condition.image_number)

if __name__ == "__main__":
    main()
