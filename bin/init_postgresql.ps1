# 1) 비밀번호 세션 변수에 설정 (한 번만)
$env:PGPASSWORD = 'nmuser'

# 2) 테이블 생성 SQL
$tableSql = @"
CREATE TABLE IF NOT EXISTS dicom_transfer_logs (
  id           SERIAL         PRIMARY KEY,
  run_time     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
  study_uid    TEXT            NOT NULL,
  step         TEXT            NOT NULL,    -- 'FIND' 또는 'MOVE'
  exit_code    INTEGER         NOT NULL,    -- 프로세스 종료 코드(0=성공)
  success      BOOLEAN         NOT NULL,    -- exit_code=0 여부
  message      TEXT            NULL         -- STDOUT/STDERR 요약
);
"@

# 3) psql 호출하여 테이블 생성
psql -h localhost `
     -U nmuser `
     -d rpacs `
     -c $tableSql

# 4) 권한 확인(필요 시)
psql -h localhost `
     -U nmuser `
     -d rpacs `
     -c "\dt dicom_transfer_logs"
