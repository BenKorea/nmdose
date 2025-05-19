#!/usr/bin/env python3
# scripts/findscu_test.py

import subprocess
import re
import sys
from pathlib import Path

# — src 폴더를 sys.path에 추가 (프로젝트 루트에 맞게 조정하세요)
project_root = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(project_root))

from nmdose.config_loader import get_config, get_pacs_config

def main():
    # 1) 실행 모드 읽어서 PACS 선택
    CONFIG      = get_config()
    PACS_all = get_pacs_config()
    if CONFIG.running_mode.lower() == "simulation":
        PACS = PACS_all.simulation
    else:
        PACS = PACS_all.clinical
    print(f"▶ Running mode: {CONFIG.running_mode} → using PACS: {PACS.aet}@{PACS.ip}:{PACS.port}")

    # 2) 여기서부터는 원하는 findscu 인자를 직접 cmd 리스트에 입력하세요
    cmd = [
        "findscu",
        "-v", "-S",
        "-aet", PACS.aet,          # 내 AET
        "-aec", PACS.aet,          # 원격 AET (같은 경우가 많음)
        PACS.ip, str(PACS.port),   # PACS IP, Port
        "-k", "QueryRetrieveLevel=STUDY",
        "-k", "StudyDate=20250101-20250502",
        "-k", "ModalitiesInStudy=PT",
        "-k", "StudyInstanceUID="
    ]

    # 3) 실행 및 결과 파싱
    print(f"▶ 실행 커맨드: {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    uids = re.findall(r'\(0020,000d\) UI \[([^\]]+)\]', output)

    # 4) 결과 출력
    print(f"▶ 응답 UID 개수: {len(uids)}")
    for uid in uids:
        print(uid)

if __name__ == "__main__":
    main()
