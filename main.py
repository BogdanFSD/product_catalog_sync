import argparse
import logging
from models import create_tables
from importer import import_feed_csv
from synchronizer import synchronize_portal

# Configure logging for the application.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Application started.")

    parser = argparse.ArgumentParser(description="CSV Importer & Synchronizer")
    parser.add_argument("--feed", required=True, help="Path to feed_items.csv")
    parser.add_argument("--portal", help="Path to portal_items.csv (optional)")
    parser.add_argument("--client", type=int, default=1, help="Client ID")
    args = parser.parse_args()

    # Create tables if they do not exist.
    create_tables()

    # 1) Import feed CSV.
    import_feed_csv(args.feed, args.client)
    logger.info("Feed CSV import completed for client %s.", args.client)

    # 2) If a portal CSV is provided, perform synchronization.
    if args.portal:
        logger.info("Starting portal synchronization for client %s.", args.client)
        synchronize_portal(args.portal, args.client)
        logger.info("Portal synchronization completed for client %s.", args.client)

    logger.info("Application finished.")

if __name__ == "__main__":
    main()
