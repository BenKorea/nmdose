#!/usr/bin/env python3
"""
schedule.py

프로젝트 최상위의 config/schedule.yaml 파일에서 스케줄링 옵션을 읽어오는 설정 로더 모듈입니다.
"""

from pathlib import Path
import yaml
from dataclasses import dataclass

@dataclass(frozen=True)
class BatchRetrievingConfig:
    """
    과거 검사들에 대한 야간 일괄 추출 작업 설정.
    Attributes:
      start_date (str): 배치 작업을 적용할 기준일 (YYYY-MM-DD)
      start_time (str): 야간 배치 시작 시간 (HH:MM)
      end_time   (str): 야간 배치 종료 시간 (HH:MM)
      number_of_studies_per_batch (int): 한 번에 처리할 최대 건수
    """
    start_date: str
    start_time: str
    end_time: str
    batch_days: int

@dataclass(frozen=True)
class DailyRetrievingConfig:
    """
    날마다 신규검사를 주간에 추출하는 작업 설정.
    Attributes:
      start_date   (str): 자동 수집 시작일 (YYYY-MM-DD)
      start_time   (str): 주간 수집 시작 시간 (HH:MM)
      end_time     (str): 주간 수집 종료 시간 (HH:MM)
      time_interval (int): 수집 간격(분 단위)
    """
    start_date: str
    start_time: str
    end_time: str
    time_interval: int

@dataclass(frozen=True)
class ScheduleConfig:
    """
    schedule.yaml 에 정의된 모든 스케줄링 옵션.
    Attributes:
      batch_retrieving (BatchRetrievingConfig)
      daily_retrieving (DailyRetrievingConfig)
    """
    batch_retrieving: BatchRetrievingConfig
    daily_retrieving: DailyRetrievingConfig

# 모듈 수준 캐시 (파일 I/O 최소화)
_schedule_cache: ScheduleConfig | None = None

def get_schedule_config(base_path: str = None) -> ScheduleConfig:
    """
    config/schedule.yaml 파일을 읽어 ScheduleConfig 객체로 반환합니다.
    반복 호출 시 캐시된 객체를 재사용합니다.

    Args:
      base_path (str, optional): schedule.yaml 이 있는 디렉터리 경로.
                                 지정하지 않으면 이 파일 위치에서
                                 세 단계 상위(프로젝트 루트)로 올라가 config/ 폴더를 기본으로 사용합니다.

    Returns:
      ScheduleConfig: 읽어들인 스케줄링 옵션을 담은 불변 데이터 클래스 인스턴스.

    Raises:
      FileNotFoundError: schedule.yaml 파일이 없을 때.
      KeyError: 필수 키가 누락되었을 때.
      ValueError: 값이 올바른 타입/포맷이 아닐 때.
    """
    global _schedule_cache
    if _schedule_cache is None:
        # 설정 파일이 위치한 config 디렉터리 결정
        if base_path:
            cfg_dir = Path(base_path)
        else:
            cfg_dir = Path(__file__).parents[3] / "config"
        cfg_file = cfg_dir / "schedule.yaml"
        if not cfg_file.is_file():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {cfg_file}")

        data = yaml.safe_load(cfg_file.read_text(encoding="utf-8-sig"))

        # batch_retrieving 파싱
        try:
            b = data["batch_retrieving"]
            batch_cfg = BatchRetrievingConfig(
                start_date=b["start_date"],
                start_time=b["start_time"],
                end_time=b["end_time"],
                batch_days=int(b["batch_days"]),
            )
        except KeyError as e:
            raise KeyError(f"schedule.yaml의 batch_retrieving 설정이 잘못되었습니다: {e}")

        # daily_retrieving 파싱
        try:
            d = data["daily_retrieving"]
            daily_cfg = DailyRetrievingConfig(
                start_date=d["start_date"],
                start_time=d["start_time"],
                end_time=d["end_time"],
                time_interval=int(d["time_interval"]),
            )
        except KeyError as e:
            raise KeyError(f"schedule.yaml의 daily_retrieving 설정이 잘못되었습니다: {e}")

        _schedule_cache = ScheduleConfig(
            batch_retrieving=batch_cfg,
            daily_retrieving=daily_cfg,
        )

    return _schedule_cache

