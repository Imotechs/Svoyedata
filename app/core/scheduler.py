# app/core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from app.services.fetcher import fetch_and_store
scheduler = AsyncIOScheduler()

async def monthly_fetch_job():
    now = datetime.now()
    print(f"Running monthly data fetch for {now:%Y-%m-%d}")
    try:
        await fetch_and_store(now.year, now.month, 1)
    except Exception as e:
        pass #print(f" Monthly fetch failed: {e}")


def init_scheduler():
    scheduler.add_job(monthly_fetch_job, "cron", day=1, hour=3)
    scheduler.start()