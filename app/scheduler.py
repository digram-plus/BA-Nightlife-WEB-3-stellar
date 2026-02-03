import os, asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .scrapers.telegram_scraper import fetch_and_store
from .scrapers.venti_parser import run as venti_run
from .scrapers.passline_parser import run as passline_run
from .scrapers.catpass_parser import run as catpass_run
from .scrapers.bombo_parser import run as bombo_run
from .scrapers.instagram_scraper import run as instagram_basic_run
from .scrapers.instagram_playwright import run as instagram_playwright_run
from .publisher.bot_publisher import run_publisher
from .config import Config

async def instagram_job(limit=10):
    mode = os.getenv("INSTAGRAM_SCRAPE_MODE", "basic").lower()
    if mode == "playwright":
        await instagram_playwright_run(limit=limit)
    else:
        # instaloader is synchronous
        instagram_basic_run(limit=limit)

def _hhmm(s):
    h,m = map(int, s.split(":")); 
    return {"hour": h, "minute": m}

async def start_scheduler():
    sch = AsyncIOScheduler(timezone=Config.TZ)
    sch.add_job(fetch_and_store, "interval", minutes=45, kwargs={"limit": 10})
    sch.add_job(venti_run, "interval", hours=3, kwargs={"limit": 10})
    sch.add_job(passline_run, "interval", hours=3, minutes=10, kwargs={"limit": 10})
    sch.add_job(catpass_run, "interval", hours=3, minutes=20, kwargs={"limit": 10})
    sch.add_job(bombo_run, "interval", hours=3, minutes=30, kwargs={"limit": 10})
    sch.add_job(instagram_job, "interval", hours=6, kwargs={"limit": 10})
    sch.add_job(run_publisher, "interval", minutes=30)
    
    if Config.ENABLE_STORIES:
        from .stories.post import send_story
        sch.add_job(send_story, CronTrigger(**_hhmm(Config.STORY_MORNING)))
        sch.add_job(send_story, CronTrigger(**_hhmm(Config.STORY_EVENING)))
    
    sch.start()
    while True:
        await asyncio.sleep(3600)
