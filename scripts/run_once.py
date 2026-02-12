import asyncio
import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("run_once")

load_dotenv()

from app.scrapers.telegram_scraper import fetch_and_store
from app.scrapers.venti_parser import run as venti_run
from app.scrapers.passline_parser import run as passline_run
from app.scrapers.catpass_parser import run as catpass_run
from app.scrapers.bombo_parser import run as bombo_run
from app.publisher.bot_publisher import run_publisher

async def main():
    logger.info("--- STARTING FULL SCRAPE CYCLE ---")
    
    # Run all scrapers to fill the DB with fresh events
    scrapers = [
        ("Telegram", fetch_and_store),
        ("Venti", venti_run),
        ("Passline", passline_run),
        ("Catpass", catpass_run),
        ("Bombo", bombo_run)
    ]
    
    for name, scraper_func in scrapers:
        try:
            logger.info(f"Running {name} scraper...")
            if asyncio.iscoroutinefunction(scraper_func):
                await scraper_func(limit=20)
            else:
                scraper_func(limit=20)
        except Exception as e:
            logger.error(f"Error in {name} scraper: {e}")

    logger.info("--- SCRAPING FINISHED ---")
    
    # Now publish the first batch of 10 events
    try:
        logger.info("Publishing 10 events...")
        await run_publisher()
    except Exception as e:
        logger.error(f"Error in publisher: {e}")
        
    except Exception as e:
        logger.error(f"Critical error during run_once: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
