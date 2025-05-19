#!/usr/bin/env python
# scripts/discover_tags.py

from nmdose.config_loader import get_config, get_pacs_config, get_retrieve_config
from nmdose.tasks.findscu_core import discover_allowed_tags
from nmdose.utils import make_batch_date_range

if __name__ == "__main__":
    CONFIG     = get_config()
    PACS    = get_pacs_config()
    RETRIEVE_CONFIG    = get_retrieve_config()
    source, target = (
        (PACS.research, PACS.simulation)
        if CONFIG.running_mode.lower() == "simulation"
        else (PACS.research, PACS.clinical)
    )

    modalities = RETRIEVE_CONFIG.clinical_to_research.modalities
    standard_tags = [
        "0008,0005", "0008,0020", "0008,0030", "0008,0050",
        "0010,0010", "0010,0020", "0020,000D", "0008,0061",
        "0008,0062", "0008,1030", "0020,1206", "0020,1208"
    ]

    # 한 줄로 모든 로직 실행
    allowed = discover_allowed_tags(source, target, modalities, standard_tags)
    print(f"\n✔ Saved {len(allowed)} allowed tags to config/allowed_tags.yaml")
