import pytest
import yaml
from pathlib import Path

# Import the function to test
from nmdose.tasks.findscu_core import discover_allowed_tags

# Dummy PACS endpoint class
class DummyPACS:
    def __init__(self, aet="SRC", ip="127.0.0.1", port=11112):
        self.aet = aet
        self.ip = ip
        self.port = port

def test_discover_allowed_tags_writes_expected(tmp_path, monkeypatch):
    """
    discover_allowed_tags should call run_findscu_query for each modality,
    aggregate returned tags, save to YAML, and return the sorted tag list.
    """
    # Prepare dummy endpoints and parameters
    source = DummyPACS(aet="SRC", ip="1.2.3.4", port=104)
    target = DummyPACS(aet="DST", ip="5.6.7.8", port=105)
    modalities = ["PT", "NM"]
    standard_tags = ["0008,0020", "0010,0010", "0020,000D"]

    # Dummy responses for each modality
    dummy_responses = {
        "PT": {"0008,0020": ("DA", "20200101"), "0020,000D": ("UI", "1.2.3")},
        "NM": {"0010,0010": ("PN", "TestName"), "0020,000D": ("UI", "4.5.6")}
    }

    # Monkeypatch run_findscu_query to return dummy data based on modality
    def fake_run_findscu_query(src, tgt, dr, mods, tags):
        # mods is a list with single modality
        return dummy_responses[mods[0]]

    monkeypatch.setattr(
        "nmdose.tasks.findscu_core.run_findscu_query",
        fake_run_findscu_query
    )

    # Define output path
    output_file = tmp_path / "allowed_tags.yaml"
    # Call the function under test
    allowed = discover_allowed_tags(
        source, target, modalities, standard_tags, output_path=str(output_file)
    )

    # Expected aggregated tags: union of keys
    expected = sorted({"0008,0020", "0020,000D", "0010,0010"})
    assert allowed == expected

    # Verify YAML file content
    content = yaml.safe_load(output_file.read_text(encoding="utf-8"))
    assert content["allowed_tags"] == expected
