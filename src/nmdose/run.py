"""
nmdose FastAPI 실행 스크립트

기능:
- 명령행 인자를 통해 로그 레벨과 인증 모드를 설정
- 인증 모드에 따라 HTTPS 적용 여부 결정
- FastAPI 앱(nmdose.main:app)을 Uvicorn으로 실행

사용법:
    python src/nmdose/run.py [--loglevel LEVEL] [--auth-mode MODE]

인자 설명:
    --loglevel   로그 레벨 (기본값: info)
                 선택값: debug, info, warning, error, critical

    --auth-mode  인증 방식 (기본값: dev)
                 - dev: 인증 미적용 (HTTP)
                 - keycloak: Keycloak 인증 적용 (HTTPS, 인증서 필요)

환경 변수:
    NMDOSE_LOGLEVEL, NMDOSE_AUTH_MODE

주의:
- keycloak 모드는 certs/server.crt, certs/server.key 파일이 필요합니다.
"""

# ───── 표준 라이브러리 ─────
import argparse
import logging
import os
from pathlib import Path

# ───── 서드파티 라이브러리 ─────
import uvicorn

# ───── 로컬 라이브러리 ─────
from nmdose.security.keycloak_config import get_keycloak_settings

# ───── 로거 객체 생성 ─────
log = logging.getLogger(__name__)


def main():
    # 1. 인자 파싱
    parser = argparse.ArgumentParser(description="nmdose FastAPI 서버 실행")
    parser.add_argument("--loglevel", default="info", choices=["debug", "info", "warning", "error", "critical"])
    parser.add_argument("--auth-mode", default="dev", choices=["dev", "keycloak"],
                        help="인증 모드 지정: dev(인증 없음), keycloak(보안 적용)")
    args = parser.parse_args()
    os.environ["NMDOSE_LOGLEVEL"] = args.loglevel.upper()
    os.environ["NMDOSE_AUTH_MODE"] = args.auth_mode

    # 2. 로깅 설정
    logging.basicConfig(
        level=args.loglevel.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s ▶ %(message)s"
    )

    logging.getLogger("uvicorn").setLevel(args.loglevel.upper())
    logging.getLogger("uvicorn.error").setLevel(args.loglevel.upper())
    logging.getLogger("uvicorn.access").setLevel(args.loglevel.upper())

    log.info(f"환경변수 NMDOSE_LOGLEVEL = {os.environ['NMDOSE_LOGLEVEL']}")
    log.info(f"▶ 인증 모드: {os.environ['NMDOSE_AUTH_MODE']}")

    # 3. Keycloak 설정 로드
    kc_settings = get_keycloak_settings()
    log.info(f"▶ Keycloak 설정: {'활성화됨' if kc_settings['enabled'] else '비활성화됨'}")

    # 4. HTTPS 조건부 설정
    use_https = args.auth_mode == "keycloak"
    cert_dir = Path(__file__).resolve().parents[2] / "certs"
    ssl_certfile = cert_dir / "server.crt"
    ssl_keyfile = cert_dir / "server.key"

    if use_https:
        if not ssl_certfile.is_file() or not ssl_keyfile.is_file():
            log.error("❌ 인증 모드 'keycloak'이지만 인증서 파일이 없습니다.")
            log.error(f"  → {ssl_certfile}")
            log.error(f"  → {ssl_keyfile}")
            raise FileNotFoundError("SSL 인증서가 필요합니다.")
        log.info("✅ HTTPS 활성화: 인증서 적용됨")
    else:
        ssl_certfile = None
        ssl_keyfile = None
        log.info("⚠ HTTPS 비활성화: HTTP로 실행됩니다")

    # 5. 서버 실행
    uvicorn.run(
        "nmdose.main:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
        log_level=args.loglevel,
        ssl_certfile=str(ssl_certfile) if use_https else None,
        ssl_keyfile=str(ssl_keyfile) if use_https else None
    )


if __name__ == "__main__":
    main()
