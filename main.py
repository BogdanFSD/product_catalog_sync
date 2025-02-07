import argparse
import os
from models import create_tables
from importer import import_feed_csv

def main():
    parser = argparse.ArgumentParser(description="Basic CSV to DB importer")
    parser.add_argument("--feed", required=True, help="Path to feed_items.csv")
    parser.add_argument("--client", type=int, default=1, help="Client ID")
    args = parser.parse_args()

    # Create table if not exists
    create_tables()

    # Import feed CSV
    import_feed_csv(args.feed, args.client)

if __name__ == "__main__":
    main()
