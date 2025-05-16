#!/usr/bin/env python
# scripts/findscu_preview.py

import re
import subprocess
from datetime import datetime
import textwrap        # ← 추가
import psycopg2

from nmdose.env.init import init_environment
from nmdose.tasks.findscu_core import run_findscu_query, parse_findscu_output


def parse_findscu_output(raw_output: str) -> list[dict[str, str]]:
    """
    raw_output: findscu 전체 stdout/stderr
    반환: Find Response 하나당 {tag: value, ...} 의 리스트
    """

    print("[DEBUG] ★ raw_output 시작 ★")
    print(textwrap.indent(raw_output, "  "))
    print("[DEBUG] ★ raw_output 끝 ★\n")
    split_pattern = re.compile(r"I: *-+[\r\n]+I: Find Response:.*")
    blocks = split_pattern.split(raw_output)
    print(f"[DEBUG] split into {len(blocks)} blocks (incl. request header)")
    response_blocks = blocks[1:]  # 첫 블록은 요청부이므로 건너뛴다
    print(f"[DEBUG] response_blocks count: {len(response_blocks)}\n")

    tag_pattern = re.compile(r'\(([0-9A-Fa-f]{4},[0-9A-Fa-f]{4})\)\s+\w{2}\s+\[([^\]]*)\]')
    parsed = []
    for i, block in enumerate(response_blocks, 1):
        print(f"[DEBUG] --- response_block #{i} start ---")
        print(textwrap.indent(block, "    "))
        matches = tag_pattern.findall(block)
        print(f"[DEBUG]   tag_pattern.findall → {len(matches)} matches: {matches}")
        print(f"[DEBUG] --- response_block #{i} end ---\n")
        attrs: dict[str, str] = {}
        for tag, val in tag_pattern.findall(block):
            # attrs[tag] = val.strip()
            tag_norm = tag.upper()
            attrs[tag_norm] = val.strip()
        parsed.append(attrs)

    print(f"[DEBUG] parse_findscu_output returning {len(parsed)} dict(s)")
    for idx, d in enumerate(parsed,1):
        print(f"[DEBUG]   parsed[{idx}]: {d}")    

    return parsed


def main():
    # ─── Load settings and environment ──────────────────────────
    cfg, calling, called, modalities, date_range, conn, log_dir = init_environment()

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
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration_ms = int((datetime.now() - ts_start).total_seconds() * 1000)

        stdout = (result.stdout or "") + (result.stderr or "")
        print(f"▶ Completed in {duration_ms} ms, return code {result.returncode}")
        print("▶ RAW OUTPUT:")
        print(stdout)

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
            study_date    = (
                datetime.strptime(attrs.get("0008,0020", ""), "%Y%m%d").date()
                if attrs.get("0008,0020") else None
            )
            study_time    = (
                datetime.strptime(attrs.get("0008,0030", ""), "%H%M%S").time()
                if attrs.get("0008,0030") else None
            )
            patient_id    = attrs.get("0010,0020")
            patient_name  = attrs.get("0010,0010")
            modalities_in = attrs.get("0008,0061")
            num_series    = int(attrs.get("0020,1206") or 0)
            num_instances = int(attrs.get("0020,1208") or 0)
            study_desc    = attrs.get("0008,1030")

            # ─── ➋ Insert into preview table ───────────────────
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO study_metadata_preview (
                        study_instance_uid,
                        find_id,
                        study_date,
                        study_time,
                        patient_id,
                        patient_name,
                        modalities,
                        num_series,
                        num_instances,
                        study_description
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (study_instance_uid) DO NOTHING
                """, (
                    study_uid,
                    None,  # find_id는 아직 없으므로 NULL
                    study_date,
                    study_time,
                    patient_id,
                    patient_name,
                    modalities_in,
                    num_series,
                    num_instances,
                    study_desc,
                ))
            conn.commit()

            # ─── ➌ Print to console ───────────────────────────
            print(f"\n--- Study #{idx} ---")
            for tag, val in attrs.items():
                print(f"({tag}) = {val}")

    conn.close()


if __name__ == "__main__":
    main()
