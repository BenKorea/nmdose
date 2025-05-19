import re
import subprocess
from pathlib import Path
from datetime import datetime

from nmdose.config_loader import (
    get_config,
    get_pacs_config,
    get_retrieve_config,
    get_schedule_config,
)
from nmdose.utils import (
    make_batch_date_range,
)


def init_environment():
    CONFIG = get_config()
    PACS = get_pacs_config()
    RETRIEVE_CONFIG = get_retrieve_config()
    SCHEDULE_CONFIG = get_schedule_config()

    log_dir = Path(r"C:\nmdose\logs\batch")
    log_dir.mkdir(parents=True, exist_ok=True)

    return CONFIG, PACS, RETRIEVE_CONFIG, SCHEDULE_CONFIG, log_dir


def select_pacs(CONFIG, PACS):
    if CONFIG.running_mode.lower() == "simulation":
        return PACS.research, PACS.simulation
    else:
        return PACS.research, PACS.clinical


def run_process(cmd: list[str]) -> tuple[str, str]:
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        std_text = (result.stdout or "") + (result.stderr or "")
        status = "SUCCESS"
    except subprocess.CalledProcessError as e:
        std_text = (e.stdout or "") + (e.stderr or "")
        status = "FAILURE"
    return std_text, status


def save_logs(log_dir, mode, modality: str, ts_start: datetime, std_text: str):
    ts_str = ts_start.strftime("%Y%m%d_%H%M%S")
    sanitized = std_text.replace("\x00", "")
    path = log_dir / f"{mode}_full_{modality}_{ts_str}.log"
    path.write_text(sanitized, encoding="utf-8")
    print(f"  Full log → {path}")


def run_findscu():
    """C-FIND 검색을 수행하고 전체 응답과 UID 리스트를 반환합니다."""
    CONFIG, PACS, RETRIEVE_CONFIG, SCHEDULE_CONFIG, log_dir = init_environment()
    print(f"▶ Running mode: {CONFIG.running_mode}")
    source, target = select_pacs(CONFIG, PACS)

    date_range = make_batch_date_range()
    modalities = RETRIEVE_CONFIG.clinical_to_research.modalities

    all_responses = []  # 전체 응답 저장
    all_uids = []

    # 정의된 Study 레벨 태그 목록
    study_tags = [
        "0008,0005", "0008,0020", "0008,0030", "0008,0050",
        "0010,0010", "0010,0020", "0020,000D", "0008,0061",
        "0008,0062", "0008,1030", "0020,1206", "0020,1208"
    ]

    for modality in modalities:
        print(f"\n=== Modality: {modality} ===")

        cmd = [
            "findscu", "-v", "-S",
            "-aet", source.aet, "-aec", target.aet,
            target.ip, str(target.port),
            "-k", "QueryRetrieveLevel=STUDY",
            "-k", f"StudyDate={date_range}",
            "-k", f"ModalitiesInStudy={modality}"
        ]
        # 모든 Study 레벨 태그 요청
        for tag in study_tags:
            cmd.extend(["-k", f"{tag}="])

        print("▶ C-FIND:", " ".join(cmd))

        ts_start = datetime.now()
        std_text, status = run_process(cmd)
        
        # 전체 응답 로그 저장
        save_logs(log_dir, "findscu", modality, ts_start, std_text)

        # stdout 전체 출력
        print("▶ Full Response:\n" + std_text)

        # 태그별 파싱
        responses = re.findall(r'\(([0-9A-Fa-f]{4},[0-9A-Fa-f]{4})\)\s+([A-Za-z]{2})\s+\[([^\]]*)\]', std_text)
        for tag, vr, val in responses:
            all_responses.append((tag, vr, val))
            if tag == "0020,000D":
                all_uids.append(val)

        print(f"  Found {len([v for t,_,v in responses if t=='0020,000D'])} UIDs")

    return all_responses, all_uids
