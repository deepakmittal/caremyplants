"""
cron.py
-------
Standalone cronjob runner for garden AI processing.

Usage:
    python3 cron.py

Environment variables:
    CRON_INTERVAL_MINUTES  How often to run the job (default: 5)
    LOG_LEVEL              Logging level (default: INFO)

The job finds all gardens with status='New' and runs the full AI pipeline
on each one (garden overview → plant identification → per-plant diagnosis).
"""

import os
import time
import logging
import logging.handlers
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

# ── Logging setup ─────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.getcwd(), "logs", "cron")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "cron.log")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Configure root logger to handle both console and file
root_logger = logging.getLogger()
root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# File handler with rotation (10MB per file, keep 5 backups)
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5
)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
root_logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
root_logger.addHandler(console_handler)

logger = logging.getLogger("garden_cron")

CRON_INTERVAL_SECONDS = int(os.getenv("CRON_INTERVAL_SECONDS", "10"))

def run_garden_processing_job() -> None:
    """
    Cronjob task: open a DB session, process all New gardens, close session.
    """
    from database import SessionLocal
    from services.garden_processor import process_new_gardens

    logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cronjob triggered")
    db = SessionLocal()
    try:
        count = process_new_gardens(db)
        logger.info(f"Cronjob complete — {count} garden(s) processed.")
    except Exception as e:
        logger.error(f"Cronjob failed with error: {e}", exc_info=True)
    finally:
        db.close()


def main() -> None:
    logger.info(
        f"Garden cronjob starting — interval: every {CRON_INTERVAL_SECONDS} second(s)"
    )

    # Run once immediately on startup so we don't wait for the first interval
    run_garden_processing_job()

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_garden_processing_job,
        trigger="interval",
        seconds=CRON_INTERVAL_SECONDS,
        id="garden_processing",
        name="Garden AI Processing",
        replace_existing=True,
    )

    logger.info("Scheduler started. Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Cronjob scheduler stopped.")


if __name__ == "__main__":
    main()
