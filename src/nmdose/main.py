# src/nmdose/main.py

# ───── 표준 라이브러리 ─────
import sys
import logging
import subprocess
from pathlib import Path

# ───── 서드파티 라이브러리 ─────
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# ───── 내부 모듈 ─────
from nmdose.env.init import init_environment

# ───── 로거 객체 생성 ─────
log = logging.getLogger(__name__)


# 1) 애플리케이션 환경 초기화 (PACS 정보, 날짜범위, 로그경로 등)
CALLING, CALLED, MODALITIES, DATE_RANGE, LOG_DIR = init_environment()

# 2) FastAPI 앱 및 템플릿 엔진 설정
app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 3) 라우터: 대시보드 페이지 렌더링
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    log.debug("▶ 대시보드 호출됨")
    return templates.TemplateResponse("dashboard.html", {"request": request})

# 4) 백엔드 처리: findscu_preview.py 실행 함수 (동기)
def run_findscu(calling=CALLING, called=CALLED):
    log.info(f"▶ findscu_preview.py 실행 시작: calling={calling.aet}, called={called.aet}")
    project_root = Path(__file__).resolve().parents[2]
    script_path = project_root / "scripts" / "findscu_preview.py"
    subprocess.run([sys.executable, str(script_path)], check=True)
    log.info("▶ findscu_preview.py 실행 완료")

# 5) 라우터: API 호출 시 findscu 백그라운드 실행
@app.post("/api/start-findscu")
async def start_findscu(background_tasks: BackgroundTasks):
    log.info("▶ /api/start-findscu 호출됨")
    background_tasks.add_task(run_findscu)
    return {"status": "started"}
