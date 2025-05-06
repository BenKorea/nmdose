#!/usr/bin/env python3
"""
pacs_test.py

PACS 설정 로더(get_pacs_config)를 테스트하는 간단한 스크립트입니다.
"""

from nmdose.config_loader.pacs import get_pacs_config

def main():
    pacs = get_pacs_config()

    print("=== PACS Settings ===")
    print(f"clinical   = AET: {pacs.clinical.aet}, IP: {pacs.clinical.ip}, Port: {pacs.clinical.port}")
    print(f"simulation = AET: {pacs.simulation.aet}, IP: {pacs.simulation.ip}, Port: {pacs.simulation.port}")
    print(f"research   = AET: {pacs.research.aet}, IP: {pacs.research.ip}, Port: {pacs.research.port}")
    print(f"dose       = AET: {pacs.dose.aet}, IP: {pacs.dose.ip}, Port: {pacs.dose.port}")

if __name__ == "__main__":
    main()
