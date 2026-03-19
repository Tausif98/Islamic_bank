from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Celery runs in a SEPARATE process from FastAPI.
# It connects to Redis as broker (job queue) and result backend (job status/results).
celery_app = Celery(
    "islamic_bank",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.profit"],       # Auto-discover tasks in these modules
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,            # STARTED state visible in result backend
    task_acks_late=True,                # Ack only after task completes (prevents lost tasks on crash)
    worker_prefetch_multiplier=1,       # Don't prefetch — important for long-running tasks
)

# ── Periodic tasks (like cron jobs) ──────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Run profit calculation every day at 00:05 UTC
    "daily-profit-distribution": {
        "task": "app.tasks.profit.distribute_daily_profit",
        "schedule": crontab(hour=0, minute=5),
    },
    # Monthly profit for investment accounts — first day of each month
    "monthly-investment-profit": {
        "task": "app.tasks.profit.distribute_monthly_investment_profit",
        "schedule": crontab(hour=1, minute=0, day_of_month=1),
    },
}