#!/usr/bin/env python
# scripts/findscu_preview.py

import re
import subprocess
from datetime import datetime

from nmdose.env.init import init_environment
from nmdose.tasks.findscu_core import run_findscu_query, parse_findscu_output

import re

def parse_findscu_output(raw_output: str) -> list[dict[str, str]]:
    """
    raw_output: findscu 전체 stdout/stderr
    반환: Find Response 하나당 {tag: value, ...} 의 리스트
    """
    # 1) '-----' 구분자와 'Find Response:' 헤더를 기준으로 블록 분리
    #    실제 dump에는 "I: ---------------------------" 다음에 "I: Find Response: N ..." 이 반복됩니다.
    #    이 둘을 묶어서 split 기준으로 사용합니다.
    split_pattern = re.compile(r"I: *-+[\r\n]+I: Find Response:.*")
    blocks = split_pattern.split(raw_output)

    # 첫 번째 블록은 요청부(Request Identifiers) 이므로 건너뛰고, 이후 블록부터 응답부
    response_blocks = blocks[1:]

    # 2) 각 블록에서 (gggg,eeee) VR [value] 패턴을 추출
    tag_pattern = re.compile(r'\(([0-9A-Fa-f]{4},[0-9A-Fa-f]{4})\)\s+\w{2}\s+\[([^\]]*)\]')
    parsed = []
    for block in response_blocks:
        attrs: dict[str,str] = {}
        for tag, val in tag_pattern.findall(block):
            attrs[tag] = val.strip()
        parsed.append(attrs)

    return parsed


def main():
    # ─── Load settings and environment ──────────────────────────
    cfg, calling, called, modalities, date_range, conn, log_dir = init_environment()

    # ─── Tags we want to probe (standard Study-level) ─────────
    standard_tags = [
        "0008,0005",  # SpecificCharacterSet
        "0008,0020",  # StudyDate
        "0008,0030",  # StudyTime
        "0008,0050",  # AccessionNumber
        "0010,0010",  # PatientName
        "0010,0020",  # PatientID
        "0020,000D",  # StudyInstanceUID
        "0008,0061",  # ModalitiesInStudy
        "0008,0062",  # SOPClassesInStudy
        "0008,1030",  # StudyDescription
        "0020,1206",  # NumberOfStudyRelatedSeries
        "0020,1208",  # NumberOfStudyRelatedInstances
    ]

    # ─── For each modality, run findscu and print results ───────
    for modality in modalities:
        print(f"\n=== Modality: {modality} ===")
        cmd = [
            "findscu", "-v", "-S",
            "-aet", calling.aet, "-aec", called.aet,
            called.ip, str(called.port),
            "-k", "QueryRetrieveLevel=STUDY",
            "-k", f"StudyDate={date_range}",
            "-k", f"ModalitiesInStudy={modality}"
        ]
        for tag in standard_tags:
            cmd += ["-k", f"{tag}="]

        print("▶ Running C-FIND:")
        print("  " + " ".join(cmd))

        ts_start = datetime.now()
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration_ms = int((datetime.now() - ts_start).total_seconds() * 1000)

        stdout = (result.stdout or "") + (result.stderr or "")
        print(f"▶ Completed in {duration_ms} ms, return code {result.returncode}")
        print("▶ RAW OUTPUT:")
        print(stdout)

        responses = parse_findscu_output(stdout)

        if not responses:
            print("⚠ 아무 응답 블록도 파싱되지 않았습니다.")
        else:
            for idx, attrs in enumerate(responses, 1):
                print(f"\n--- Study #{idx} ---")
                for tag, val in attrs.items():
                    print(f"({tag}) = {val}")



if __name__ == "__main__":
    main()
