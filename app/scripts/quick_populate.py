import asyncio
import sys
from app.scrapers import bombo_parser, venti_parser, catpass_parser, passline_parser, telegram_scraper

async def run_all():
    print("--- STARTING QUICK POPULATION (5 EVENTS PER SCRAPER) ---")
    
    # Run sync scrapers
    try:
        bombo_parser.run(limit=5, force_publish=True)
    except Exception as e:
        print(f"Error in bombo_parser: {e}")
        
    try:
        venti_parser.run(limit=5, force_publish=True)
    except Exception as e:
        print(f"Error in venti_parser: {e}")
        
    try:
        catpass_parser.run(limit=5, force_publish=True)
    except Exception as e:
        print(f"Error in catpass_parser: {e}")
        
    try:
        passline_parser.run(limit=5, force_publish=True)
    except Exception as e:
        print(f"Error in passline_parser: {e}")
        
    # Run async scraper
    try:
        await telegram_scraper.fetch_and_store(limit=5, force_publish=True)
    except Exception as e:
        print(f"Error in telegram_scraper: {e}")
        
    print("--- QUICK POPULATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(run_all())
