# src/nmdose/utils/text_utils.py

import copy

_NULL_TRANS = str.maketrans('', '', '\x00')

def strip_nuls(s: str) -> str:
    """
    문자열 s에서 모든 NUL(0x00) 문자를 제거합니다.
    """
    return s.translate(_NULL_TRANS)

def sanitize_value(x):
    """
    임의의 객체 x에 대해:
      - str 이면 NUL 제거
      - dict 이면 각 value 재귀 처리
      - list/tuple 이면 각 요소 재귀 처리
      - 그 외는 그대로 반환
    """
    if isinstance(x, str):
        return strip_nuls(x)
    if isinstance(x, dict):
        return {k: sanitize_value(v) for k, v in x.items()}
    if isinstance(x, list):
        return [sanitize_value(v) for v in x]
    if isinstance(x, tuple):
        return tuple(sanitize_value(v) for v in x)
    # 필요 시 set, etc. 도 추가 가능
    return x

def sanitize_event(event: dict) -> dict:
    """
    event 딕셔너리 전체를 복사 없이 제자리(recursive in-place)로
    문자열 값에서 NUL을 제거합니다.
    """
    for k, v in event.items():
        event[k] = sanitize_value(v)
    return event
