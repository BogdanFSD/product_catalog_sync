import argparse
import logging

from services.table_creator import TableCreator
from repository.product_repository import ProductRepository
from services.csv_reader import FeedCsvReader
from services.feed_importer import FeedImporter
from services.portal_synchronizer import PortalSynchronizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CLIParser:
    def parse_args(self):
        parser = argparse.ArgumentParser(description="CSV Importer & Synchronizer")
        parser.add_argument("--feed", required=True, help="Path to feed_items.csv")
        parser.add_argument("--portal", help="Path to portal_items.csv (optional)")
        parser.add_argument("--client", type=int, default=1, help="Client ID")
        return parser.parse_args()

class Application:
    def __init__(self, table_creator, feed_importer_factory, portal_synchronizer_factory):
        self.table_creator = table_creator
        self.feed_importer_factory = feed_importer_factory
        self.portal_synchronizer_factory = portal_synchronizer_factory

    def run(self, feed_file, portal_file, client_id):
        logger.info("Application started.")

        self.table_creator.create_tables()

        feed_importer = self.feed_importer_factory()
        feed_importer.import_feed(feed_file, client_id)
        logger.info("Feed CSV import completed for client %s.", client_id)

        if portal_file:
            logger.info("Starting portal synchronization for client %s.", client_id)
            synchronizer = self.portal_synchronizer_factory()

            portal_records = synchronizer.read_portal_csv(portal_file)
            if not portal_records:
                logger.info("No valid portal records found in CSV.")
            else:
                db_products = synchronizer.fetch_db_products(client_id)
                to_delete, to_insert, to_update = synchronizer.compute_sync_actions(db_products, portal_records)
                synchronizer.apply_sync_actions(client_id, to_delete, to_insert, to_update)
                logger.info("Portal synchronization completed for client %s.", client_id)

        logger.info("Application finished.")

def main():
    cli_parser = CLIParser()
    args = cli_parser.parse_args()

    table_creator = TableCreator()

    def feed_importer_factory():
        repository = ProductRepository()
        csv_reader = FeedCsvReader()
        return FeedImporter(repository, csv_reader)

    def portal_synchronizer_factory():
        return PortalSynchronizer()

    app = Application(
        table_creator=table_creator,
        feed_importer_factory=feed_importer_factory,
        portal_synchronizer_factory=portal_synchronizer_factory
    )

    app.run(
        feed_file=args.feed,
        portal_file=args.portal,
        client_id=args.client
    )

if __name__ == "__main__":
    main()
