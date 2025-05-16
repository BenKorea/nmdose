import re
import subprocess
from datetime import datetime
import yaml

from nmdose.utils import make_batch_date_range


def run_findscu_query(source, target, date_range, modalities, tags):
    """
    실행: findscu C-FIND, Study 레벨.
    반환: {tag: (VR, value), ...}
    """
    ts_start = datetime.now()
    print(f"[DEBUG] run_findscu_query START: {ts_start}")

    cmd = [
        'findscu', '-v', '-S',
        '-aet', source.aet, '-aec', target.aet,
        target.ip, str(target.port),
        '-k', f'StudyDate={date_range}'
    ]
    for m in modalities:
        cmd.extend(['-k', f'ModalitiesInStudy={m}'])
    for tag in tags:
        cmd.extend(['-k', f'{tag}='])

    print(f"[DEBUG] Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        stdout = (result.stdout or '') + (result.stderr or '')
        status = 'SUCCESS' if result.returncode == 0 else f'FAIL:{result.returncode}'
    except Exception as e:
        stdout = ''
        status = f'EXCEPTION: {e}'

    print(f"[DEBUG] stdout:\n{stdout}")
    print(f"[DEBUG] Status: {status}")

    ts_end = datetime.now()
    dur = (ts_end - ts_start).total_seconds() * 1000
    print(f"[DEBUG] run_findscu_query END: {ts_end} ({dur:.0f}ms)")

    matches = re.findall(
        r'\(([0-9A-Fa-f]{4},[0-9A-Fa-f]{4})\)\s+(\w{2})\s+\[([^\]]*)\]',
        stdout
    )
    print(f"[DEBUG] Parsed {len(matches)} items")
    return {tag: (vr, val) for tag, vr, val in matches}


def discover_allowed_tags(source, target, modalities, standard_tags, output_path="config/allowed_tags.yaml"):
    """
    Modality별 run_findscu_query 호출하여 허용 태그 합집합 저장
    반환: sorted allowed tag list
    """
    allowed = set()
    date_range = make_batch_date_range()
    print(f"[DISCOVER] Date range: {date_range}")
    for mod in modalities:
        print(f"[DISCOVER] Modality: {mod}")
        resp = run_findscu_query(source, target, date_range, [mod], standard_tags)
        print(f"  → Found {len(resp)} tags: {sorted(resp.keys())}")
        allowed.update(resp.keys())

    allowed = sorted(allowed)
    print(f"[DISCOVER] Total tags: {len(allowed)}")
    for tag in allowed:
        print(f"  {tag}")

    # save
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump({"allowed_tags": allowed}, f, default_flow_style=False, allow_unicode=True)
    return allowed


def parse_findscu_output(raw_output):
    """
    아직 구현 대기 중인 파싱 함수.
    raw_output 문자열을 받아 그대로 반환하거나,
    빈 리스트를 반환하도록 해둡니다.
    """
    # TODO: 실제 파싱 로직을 여기에 구현할 것
    return []  # 현재는 아무 동작도 하지 않음