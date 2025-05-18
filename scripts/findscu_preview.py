# scripts/findscu_preview.py

import sys
print("실행 중인 파이썬 경로:", sys.executable)
import yaml
print("✅ PyYAML 정상 로딩됨")

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datetime import datetime
import subprocess
import re

from nmdose.env.init import init_environment


def get_standard_study_tags() -> list[str]:
    return [
        "0008,0005", "0008,0020", "0008,0030", "0008,0050", "0010,0010",
        "0010,0020", "0020,000D", "0008,0061", "0008,0062", "0008,1030",
        "0020,1206", "0020,1208",
    ]


def build_findscu_command(calling, called, modality, date_range, tags) -> list[str]:
    cmd = [
        "findscu", "-v", "-S",
        "-aet", calling.aet, "-aec", called.aet,
        called.ip, str(called.port),
        "-k", "QueryRetrieveLevel=STUDY",
        "-k", f"StudyDate={date_range}",
        "-k", f"ModalitiesInStudy={modality}",
    ]
    for tag in tags:
        cmd += ["-k", f"{tag}="]
    return cmd


def parse_findscu_output(raw_output: str) -> list[dict[str, str]]:
    split_pattern = re.compile(r"I: *-+[\r\n]+I: Find Response:.*")
    blocks = split_pattern.split(raw_output)
    response_blocks = blocks[1:]  # 첫 블록은 요청부


    tag_pattern = re.compile(r'\(([0-9A-Fa-f]{4},[0-9A-Fa-f]{4})\)\s+\w{2}\s+\[([^\]]*)\]')

    parsed = []
    for block in response_blocks:
        matches = tag_pattern.findall(block)
        attrs: dict[str, str] = {}
        for tag, val in matches:
            attrs[tag.upper()] = val.strip()
        parsed.append(attrs)
    return parsed


def print_study_attributes(idx: int, attrs: dict[str, str]):
    study_uid = attrs.get("0020,000D")
    print(f"[DEBUG] Response #{idx} → StudyInstanceUID: {study_uid}")
    if not study_uid:
        print(f"⚠ Skipping response #{idx}: missing StudyInstanceUID")
        return

    try:
        if "0008,0020" in attrs:
            study_date = datetime.strptime(attrs["0008,0020"], "%Y%m%d").date()
            print(f"[DEBUG] Response #{idx} → study_date: {study_date}")
    except Exception:
        print(f"[DEBUG] Response #{idx} → study_date: (parsing error)")

    try:
        if "0008,0030" in attrs:
            time_str = attrs["0008,0030"].split(".")[0]
            study_time = datetime.strptime(time_str, "%H%M%S").time()
            print(f"[DEBUG] Response #{idx} → study_time: {study_time}")
    except Exception:
        print(f"[DEBUG] Response #{idx} → study_time: (parsing error)")

    print(f"[DEBUG] Response #{idx} → patient_id: {attrs.get('0010,0020')}")
    print(f"[DEBUG] Response #{idx} → patient_name: {attrs.get('0010,0010')}")
    print(f"[DEBUG] Response #{idx} → modalities_in: {attrs.get('0008,0061')}")
    print(f"[DEBUG] Response #{idx} → num_series: {attrs.get('0020,1206')}")
    print(f"[DEBUG] Response #{idx} → num_instances: {attrs.get('0020,1208')}")
    print(f"[DEBUG] Response #{idx} → study_desc: {attrs.get('0008,1030')}")


def run_findscu_preview(modality, calling, called, date_range, standard_tags):
    print(f"\n=== Modality: {modality} ===")
    cmd = build_findscu_command(calling, called, modality, date_range, standard_tags)
    print("▶ Running C-FIND:")
    print("  " + " ".join(cmd))

    ts_start = datetime.now()
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    stdout = (result.stdout or "") + (result.stderr or "")
    responses = parse_findscu_output(stdout)

    if not responses:
        print("⚠ 아무 응답 블록도 파싱되지 않았습니다.")
        return

    for idx, attrs in enumerate(responses, 1):
        print_study_attributes(idx, attrs)


def main():
    CONFIG, calling, called, modalities, date_range, conn, log_dir = init_environment()
    tags = get_standard_study_tags()
    for modality in modalities:
        run_findscu_preview(modality, calling, called, date_range, tags)
    conn.close()


if __name__ == "__main__":
    main()
