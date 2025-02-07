import argparse
import os
from models import create_tables
from importer import import_feed_csv
from synchronizer import synchronize_portal

def main():
    parser = argparse.ArgumentParser(description="CSV Importer & Synchronizer")
    parser.add_argument("--feed", required=True, help="Path to feed_items.csv")
    parser.add_argument("--portal", help="Path to portal_items.csv (optional)")
    parser.add_argument("--client", type=int, default=1, help="Client ID")
    args = parser.parse_args()

    # Create table if not exists
    create_tables()

    # 1) Import feed CSV
    import_feed_csv(args.feed, args.client)

    # 2) If a portal CSV is provided, do synchronization
    if args.portal:
        synchronize_portal(args.portal, args.client)

if __name__ == "__main__":
    main()
