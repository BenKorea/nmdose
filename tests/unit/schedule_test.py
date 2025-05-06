#!/usr/bin/env python3
"""
schedule_test.py

schedule.py 모듈의 get_schedule_config() 함수를 호출하여
schedule.yaml에 정의된 스케줄링 설정을 출력하는 간단한 테스트 스크립트입니다.
"""

from nmdose.config_loader.schedule import get_schedule_config

def main():
    sched = get_schedule_config()

    # Batch retrieving 설정 출력
    print("=== Batch Retrieving ===")
    print(f"Start Date:                  {sched.batch_retrieving.start_date}")
    print(f"Start Time:                  {sched.batch_retrieving.start_time}")
    print(f"End Time:                    {sched.batch_retrieving.end_time}")
    print(f"Number of Studies per Batch: {sched.batch_retrieving.number_of_studies_per_batch}\n")

    # Daily retrieving 설정 출력
    print("=== Daily Retrieving ===")
    print(f"Start Date:   {sched.daily_retrieving.start_date}")
    print(f"Start Time:   {sched.daily_retrieving.start_time}")
    print(f"End Time:     {sched.daily_retrieving.end_time}")
    print(f"Time Interval (min): {sched.daily_retrieving.time_interval}")

if __name__ == "__main__":
    main()
