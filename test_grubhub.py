"""Quick entry script to test the Grubhub ordering agent."""

import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(name)s - %(levelname)s - %(message)s",
)

from dotenv import load_dotenv

load_dotenv()

from backend.integrations.grubhub.automation import get_driver, intelligent_order

RESTAURANT = "connecting grounds"
ITEMS = "buckeye mocha"


def main():
    print(f"=== Ordering: {ITEMS} from {RESTAURANT} ===\n")

    driver = get_driver()
    time.sleep(8)  # Wait for splash + app to load

    try:
        result = intelligent_order(driver, RESTAURANT, ITEMS)
        print(f"\n{'='*40}")
        print(f"Added:    {result['added']}")
        print(f"Failed:   {result['failed']}")
        print(f"Checkout: {result['checkout_result']}")
        print(f"{'='*40}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
