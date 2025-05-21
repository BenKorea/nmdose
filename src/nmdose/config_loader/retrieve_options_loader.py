# src/nmdose/config_loader/retrieve_options_loader.py

from dataclasses import dataclass
from pathlib import Path
import yaml

CONFIG_FILE = Path(__file__).resolve().parents[3] / "config" / "retrieve_options.yaml"

@dataclass
class RetrieveToResearchConfig:
    modalities: list[str]
    enable_exclusion: bool
    excluded_tag: str
    excluded_word: str

    batch_start_date: str
    batch_start_time: str
    batch_end_time: str
    batch_days: int

    daily_start_date: str
    daily_start_time: str
    daily_end_time: str
    daily_time_interval: int

@dataclass
class RetrieveToDoseConfig:
    ct_enable_modalities_in_series: bool
    ct_modalities_in_series: list[str]

    ct_enable_series_description: bool
    ct_series_description: list[str]

    ct_enable_series_number: bool
    ct_series_number: list[str]

    pet_enable_single_axial_first_image: bool

@dataclass
class RetrieveOptions:
    retrieve_to_research: RetrieveToResearchConfig
    retrieve_to_dose: RetrieveToDoseConfig


def get_retrieve_config(path: Path = CONFIG_FILE) -> RetrieveOptions:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return RetrieveOptions(
        retrieve_to_research=RetrieveToResearchConfig(**raw["retrieve_to_research"]),
        retrieve_to_dose=RetrieveToDoseConfig(**raw["retrieve_to_dose"]),
    )
