import pytest
from nmdose.config_loader.retrieve_options_loader import get_retrieve_options_config, RetrieveOptions

def test_retrieve_options_loads_correctly():
    config = get_retrieve_options_config()

    assert isinstance(config, RetrieveOptions)

    # retrieve_to_research 검증
    rtr = config.retrieve_to_research
    assert isinstance(rtr.modalities, list)
    assert rtr.enable_exclusion is True
    assert rtr.excluded_tag == "study_description"
    assert rtr.excluded_word.lower() == "outside"

    # retrieve_to_dose 검증
    rtd = config.retrieve_to_dose
    assert rtd.ct_enable_modalities_in_series is True
    assert "SR" in rtd.ct_modalities_in_series
    assert rtd.ct_enable_series_number is True
    assert "501" in rtd.ct_series_number

def test_invalid_yaml_path_raises_error():
    from pathlib import Path
    with pytest.raises(FileNotFoundError):
        get_retrieve_options_config(Path("/invalid/path/to/file.yaml"))
