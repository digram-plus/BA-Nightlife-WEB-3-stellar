import logging
import time
import sys
import os

sys.path.append(os.getcwd())

from app.scrapers import venti_parser, bombo_parser, catpass_parser, passline_parser

# Configure logging to show info
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("tester")

def test_all():
    parsers = [
        ("Venti", venti_parser),
        ("Bombo", bombo_parser),
        ("Catpass", catpass_parser),
        ("Passline", passline_parser)
    ]

    print("\n" + "="*50)
    print("🚀 STARTING FULL SCRAPER VERIFICATION")
    print("="*50 + "\n")

    for name, module in parsers:
        try:
            print(f"\n--- Testing {name} ---")
            # Run with limit=5 to be fast
            if hasattr(module, 'run'):
                module.run(limit=5)
            else:
                print(f"❌ {name} has no 'run' function!")
        except Exception as e:
            print(f"❌ {name} FAILED: {e}")
            logger.exception(f"{name} crashed")
        
        time.sleep(1)

    print("\n" + "="*50)
    print("✅ VERIFICATION COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_all()
