"""
백그라운드 파인튜닝 스케줄러
매일 자정에 자동으로 파인튜닝 실행
"""
import schedule
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path


# 로깅 설정
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_finetuning():
    """파인튜닝 실행"""
    logger.info("🚀 파인튜닝 작업 시작")
    
    script_path = Path(__file__).parent / "finetune_slm.py"
    
    try:
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True,
            text=True,
            timeout=7200  # 2시간 타임아웃
        )
        
        if result.returncode == 0:
            logger.info("✅ 파인튜닝 성공")
            logger.info(result.stdout)
        else:
            logger.error("❌ 파인튜닝 실패")
            logger.error(result.stderr)
    
    except subprocess.TimeoutExpired:
        logger.error("⏰ 파인튜닝 타임아웃 (2시간 초과)")
    except Exception as e:
        logger.error(f"❌ 에러 발생: {e}")


def main():
    """스케줄러 메인 루프"""
    logger.info("📅 파인튜닝 스케줄러 시작")
    logger.info("⏰ 매일 자정에 실행 예정")
    
    # 매일 자정에 실행
    schedule.every().day.at("00:00").do(run_finetuning)
    
    # 테스트: 즉시 한 번 실행 (선택)
    # run_finetuning()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏹️ 스케줄러 종료")