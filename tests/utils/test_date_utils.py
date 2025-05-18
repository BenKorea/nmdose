from datetime import date
from unittest.mock import patch, MagicMock
from nmdose.utils.date_utils import make_batch_date_range

@patch("nmdose.utils.date_utils.get_schedule_config")
@patch("nmdose.utils.date_utils.get_db_config")
@patch("nmdose.utils.date_utils.psycopg2.connect")
def test_make_batch_date_range(mock_connect, mock_get_db_config, mock_get_schedule_config):
    mock_sched = MagicMock()
    mock_sched.batch_retrieving.start_date = "20220101"
    mock_sched.batch_retrieving.batch_days = 3
    mock_sched.daily_retrieving.start_date = "20220110"
    mock_get_schedule_config.return_value = mock_sched

    mock_get_db_config.return_value.rpacs = MagicMock(
        host="localhost", port=5432, user="test", password="test", database="rpacs"
    )

    # 연결과 커서 mocking
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # 핵심 수정: fetchone() → 실제 튜플 반환
    mock_cursor.fetchone.return_value = (date(2022, 1, 2),)

    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_connect.return_value.__enter__.return_value = mock_conn

    result = make_batch_date_range()
    assert result == "20220102-20220104"
