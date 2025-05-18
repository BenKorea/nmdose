#!/usr/bin/env python
# scripts/findscu_preview.py

import re
import subprocess
from datetime import datetime
import textwrap
import psycopg2

from nmdose.env.init import init_environment
from nmdose.tasks.findscu_core import run_findscu_query, parse_findscu_output


def parse_findscu_output(raw_output: str) -> list[dict[str, str]]:
    """
    raw_output: findscu 전체 stdout/stderr
    반환: Find Response 하나당 {tag: value, ...} 의 리스트
    """
    split_pattern = re.compile(r"I: *-+[\r\n]+I: Find Response:.*")
    blocks = split_pattern.split(raw_output)
    response_blocks = blocks[1:]  # 첫 블록은 요청부이므로 건너뛴다

    tag_pattern = re.compile(r'\(([0-9A-Fa-f]{4},[0-9A-Fa-f]{4})\)\s+\w{2}\s+\[([^\]]*)\]')
    parsed = []
    for i, block in enumerate(response_blocks, 1):
        matches = tag_pattern.findall(block)
        attrs: dict[str, str] = {}
        for tag, val in matches:
            tag_norm = tag.upper()
            attrs[tag_norm] = val.strip()
        parsed.append(attrs)

    return parsed


def main():
    # ─── Load settings and environment ──────────────────────────
    CONFIG, calling, called, modalities, date_range, conn, log_dir = init_environment()

    # ─── Standard Study-level tags ─────────────────────────────
    standard_tags = [
        "0008,0005",  # SpecificCharacterSet
        "0008,0020",  # StudyDate
        "0008,0030",  # StudyTime
        "0008,0050",  # AccessionNumber
        "0010,0010",  # PatientName
        "0010,0020",  # PatientID
        "0020,000D",  # StudyInstanceUID (PK, NOT NULL)
        "0008,0061",  # ModalitiesInStudy
        "0008,0062",  # SOPClassesInStudy
        "0008,1030",  # StudyDescription
        "0020,1206",  # NumberOfStudyRelatedSeries
        "0020,1208",  # NumberOfStudyRelatedInstances
    ]

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
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        duration_ms = int((datetime.now() - ts_start).total_seconds() * 1000)

        stdout = (result.stdout or "") + (result.stderr or "")
        responses = parse_findscu_output(stdout)

        if not responses:
            print("⚠ 아무 응답 블록도 파싱되지 않았습니다.")
            continue

        for idx, attrs in enumerate(responses, 1):
            study_uid = attrs.get("0020,000D")
            print(f"[DEBUG] Response #{idx} → StudyInstanceUID: {study_uid}")
            if not study_uid:
                print(f"⚠ Skipping response #{idx}: missing StudyInstanceUID")
                continue

            # ─── ➊ Extract fields ────────────────────────────────
            if attrs.get("0008,0020"):
                study_date = datetime.strptime(attrs.get("0008,0020"), "%Y%m%d").date()
                print(f"[DEBUG] Response #{idx} → study_date: {study_date}")
            else:
                study_date = None

            if attrs.get("0008,0030"):
                time_str = attrs.get("0008,0030").split(".")[0]  # ← 여기가 핵심
                study_time = datetime.strptime(time_str, "%H%M%S").time()
                print(f"[DEBUG] Response #{idx} → study_time: {study_time}")
            else:
                study_time = None


            patient_id = attrs.get("0010,0020")
            print(f"[DEBUG] Response #{idx} → patient_id: {patient_id}")
            patient_name = attrs.get("0010,0010")
            print(f"[DEBUG] Response #{idx} → patient_name: {patient_name}")
            modalities_in = attrs.get("0008,0061")
            print(f"[DEBUG] Response #{idx} → modalities_in: {modalities_in}")
            num_series = int(attrs.get("0020,1206") or 0)
            print(f"[DEBUG] Response #{idx} → num_series: {num_series}")
            num_instances = int(attrs.get("0020,1208") or 0)
            print(f"[DEBUG] Response #{idx} → num_instances: {num_instances}")
            study_desc = attrs.get("0008,1030")
            print(f"[DEBUG] Response #{idx} → study_desc: {study_desc}")

    conn.close()


if __name__ == "__main__":
    main()
