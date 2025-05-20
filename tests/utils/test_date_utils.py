# tests/test_date_utils.py

import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from nmdose.utils.date_utils import make_batch_date_range, parse_start_date, parse_end_date


@pytest.fixture
def fake_retrieve_options():
    class FakeRetrieveToResearch:
        batch_start_date = "20240101"
        batch_days = 7
        daily_start_date = "20240120"
        # 기타 필드는 무시

    class FakeRetrieveOptions:
        retrieve_to_research = FakeRetrieveToResearch()
        retrieve_to_dose = None

    return FakeRetrieveOptions()


@patch("nmdose.utils.date_utils.get_retrieve_options_config")
@patch("nmdose.utils.date_utils.psycopg2.connect")
def test_make_batch_date_range_with_last_processed_date(mock_connect, mock_get_config, fake_retrieve_options):
    # 설정 Mock
    mock_get_config.return_value = fake_retrieve_options

    # DB 결과 Mock
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [date(2024, 1, 10)]  # 마지막 처리일
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    result = make_batch_date_range()
    assert result == "20240110-20240116"


@patch("nmdose.utils.date_utils.get_retrieve_options_config")
@patch("nmdose.utils.date_utils.psycopg2.connect")
def test_make_batch_date_range_without_last_processed_date(mock_connect, mock_get_config, fake_retrieve_options):
    mock_get_config.return_value = fake_retrieve_options

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None  # 마지막 처리일 없음
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    result = make_batch_date_range()
    assert result == "20240101-20240107"


def test_parse_start_date():
    assert parse_start_date("20240101-20240107") == date(2024, 1, 1)


def test_parse_end_date():
    assert parse_end_date("20240101-20240107") == date(2024, 1, 7)
