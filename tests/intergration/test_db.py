from datetime import date
from nmdose.db_utils import record_last_processed_date

# ‘night_batch’ 작업이 2025-05-04에 완료되었음을 기록
record_last_processed_date("night_batch", date(2025, 5, 4))