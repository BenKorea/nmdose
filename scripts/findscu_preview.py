# scripts/findscu_preview.py

import sys
from pathlib import Path
from datetime import datetime
import subprocess
import re

# 환경 초기화 로직 호출 (DB는 사용하지 않으므로 init_environment에서 DB 연결은 반환되지 않습니다)
from nmdose.env.init import init_environment


def get_standard_study_tags() -> list[str]:
    """Study 조회 시 포함할 DICOM 태그 목록"""
    return [
        "0008,0005", "0008,0020", "0008,0030", "0008,0050", "0010,0010",
        "0010,0020", "0020,000D", "0008,0061", "0008,0062", "0008,1030",
        "0020,1206", "0020,1208",
    ]


def build_findscu_command(calling, called, modality, date_range, tags) -> list[str]:
    """C-FIND 명령어 빌드"""
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
    """findscu 출력 파싱"""
    split_pattern = re.compile(r"I: *-+[\r\n]+I: Find Response:.*")
    blocks = split_pattern.split(raw_output)
    response_blocks = blocks[1:]

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
    """파싱된 스터디 속성 출력"""
    study_uid = attrs.get("0020,000D")
    print(f"[DEBUG] Response #{idx} → StudyInstanceUID: {study_uid}")
    if not study_uid:
        print(f"⚠ Skipping response #{idx}: missing StudyInstanceUID")
        return

    # 날짜, 시간, 환자 정보 등 출력
    if "0008,0020" in attrs:
        try:
            study_date = datetime.strptime(attrs["0008,0020"], "%Y%m%d").date()
            print(f"[DEBUG] Response #{idx} → study_date: {study_date}")
        except Exception:
            print(f"[DEBUG] Response #{idx} → study_date: parsing error")
    if "0008,0030" in attrs:
        try:
            time_str = attrs["0008,0030"].split(".")[0]
            study_time = datetime.strptime(time_str, "%H%M%S").time()
            print(f"[DEBUG] Response #{idx} → study_time: {study_time}")
        except Exception:
            print(f"[DEBUG] Response #{idx} → study_time: parsing error")

    for tag in ["0010,0020", "0010,0010", "0008,0061", "0020,1206", "0020,1208", "0008,1030"]:
        print(f"[DEBUG] Response #{idx} → {tag.replace(',', '_')}: {attrs.get(tag)}")


def run_findscu_preview(modality, calling, called, date_range, standard_tags):
    """단일 modality에 대해 findscu 실행 및 결과 파싱"""
    print(f"\n=== Modality: {modality} ===")
    cmd = build_findscu_command(calling, called, modality, date_range, standard_tags)
    print("▶ Running C-FIND:")
    print("  " + " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    stdout = (result.stdout or "") + (result.stderr or "")
    responses = parse_findscu_output(stdout)

    if not responses:
        print("⚠ 아무 응답 블록도 파싱되지 않았습니다.")
        return

    for idx, attrs in enumerate(responses, 1):
        print_study_attributes(idx, attrs)


def main():
    # 환경 초기화 (DB 연결은 이 스크립트에서 사용하지 않으므로 제외)
    calling, called, modalities, date_range, log_dir = init_environment()
    tags = get_standard_study_tags()
    for modality in modalities:
        run_findscu_preview(modality, calling, called, date_range, tags)
    # DB 연결이 없으므로 close 호출 제거


if __name__ == "__main__":
    main()
