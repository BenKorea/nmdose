import sys
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import subprocess
from pathlib import Path

# 🔹 로깅 추가
import logging
print("🔍 sys.executable:", sys.executable)
logging.basicConfig(level=logging.DEBUG)
logging.debug("✅ 로깅이 동작 중입니다.")

from nmdose.config_loader.config_loader import get_config
from nmdose.utils.logging_utils import configure_logging

# ─────────────────────────────
# 앱 시작
app = FastAPI()

# 🔹 로깅 설정
config = get_config()
configure_logging(config.logging_mode)  # 예: "DEBUG"
log = logging.getLogger(__name__)
log.info("▶ FastAPI 앱 초기화 시작")

# 템플릿 경로 설정
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    log.debug("▶ 대시보드 호출됨")
    return templates.TemplateResponse("dashboard.html", {"request": request})

def run_findscu():
    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scripts" / "findscu_preview.py"
    log.info(f"▶ findscu_preview.py 실행: {script_path}")
    subprocess.run([sys.executable, str(script_path)])

@app.post("/api/start-findscu")
async def start_findscu(background_tasks: BackgroundTasks):
    log.info("▶ /api/start-findscu 호출됨")
    background_tasks.add_task(run_findscu)
    return {"status": "started"}
