import sys
import logging
from pathlib import Path
import subprocess

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from nmdose.env.init import init_environment  # 환경 초기화 로직 호출
from nmdose.utils.logging_utils import configure_logging

# ─────────────────────────────
# 1) 애플리케이션 환경 일괄 초기화
CALLING, CALLED, MODALITIES, DATE_RANGE, LOG_DIR = init_environment()

log = logging.getLogger(__name__)   # ← 여기에 logger 선언만 추가


# # 2) 로깅 설정
# configure_logging(CONFIG.logging_mode)
# log = logging.getLogger(__name__)
# log.info("▶ FastAPI 앱 초기화 완료")

# 3) FastAPI 앱 생성 및 템플릿 설정
app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    log.debug("▶ 대시보드 호출됨")
    # 필요 시 템플릿에 설정값 전달 가능
    return templates.TemplateResponse(
        "dashboard.html", {"request": request}
    )

def run_findscu(calling=CALLING, called=CALLED):

    log.info(f"▶ findscu_preview.py 실행 시작: calling={calling.aet}, called={called.aet}")
    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scripts" / "findscu_preview.py"
    subprocess.run([sys.executable, str(script_path)], check=True)
    log.info("▶ findscu_preview.py 실행 완료")

@app.post("/api/start-findscu")
async def start_findscu(background_tasks: BackgroundTasks):
    log.info("▶ /api/start-findscu 호출됨")
    # 백그라운드에서 findscu 작업 실행
    background_tasks.add_task(run_findscu)
    return {"status": "started"}