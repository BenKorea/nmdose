# src/nmdose/run.py

# ───── 표준 라이브러리 ─────
import argparse
import logging
import os

# ───── 서드파티 라이브러리 ─────
import uvicorn

# ───── 로거 객체 생성 ─────
log = logging.getLogger(__name__)


def main():
    # 1. 인자 파싱
    parser = argparse.ArgumentParser(description="nmdose FastAPI 서버 실행")
    parser.add_argument(
        "--loglevel",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="로깅 레벨 지정"
    )
    args = parser.parse_args()
    os.environ["NMDOSE_LOGLEVEL"] = args.loglevel.upper()

    # 2. 로깅 설정 (Python 표준)
    logging.basicConfig(
        level=args.loglevel.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s ▶ %(message)s"
    )

    # 3. Uvicorn 로그레벨 연동
    logging.getLogger("uvicorn").setLevel(args.loglevel.upper())
    logging.getLogger("uvicorn.error").setLevel(args.loglevel.upper())
    logging.getLogger("uvicorn.access").setLevel(args.loglevel.upper())

    # 로깅 레벨 명시적으로 출력
    log.info(f"환경변수 NMDOSE_LOGLEVEL = {os.environ['NMDOSE_LOGLEVEL']}")

    # 4. 서버 실행
    uvicorn.run(
        "nmdose.main:app",
        host="127.0.0.1",
        port=8001,
        reload=False,
        log_level=args.loglevel  # uvicorn 자체 log_level 옵션도 연동
    )


if __name__ == "__main__":
    main()
