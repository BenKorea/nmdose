from fastapi import APIRouter, BackgroundTasks
import subprocess

router = APIRouter()

# 실제로 실행할 함수 (서브프로세스로 별도 실행)
def run_findscu():
    try:
        subprocess.run(["python", "scripts/findscu_preview.py"], check=True)
    except subprocess.CalledProcessError as e:
        # 추후 로그 파일에 에러 저장 가능
        print(f"[ERROR] Findscu 실행 실패: {e}")

# API 라우트
@router.post("/api/start-findscu")
async def start_findscu(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_findscu)
    return {"status": "started"}
