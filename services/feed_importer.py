import logging
from db.connection import DatabaseConnection
from repository.product_repository import ProductRepository
from services.csv_reader import FeedCsvReader

logger = logging.getLogger(__name__)

db_connection = DatabaseConnection()

class FeedImporter:
    """
    Orchestrates the feed import process by reading the CSV and
    upserting records into the database using the repository.
    """

    def __init__(self, repository: ProductRepository, csv_reader: FeedCsvReader):
        self.repository = repository
        self.csv_reader = csv_reader

    def import_feed(self, csv_path: str, client_id: int):
        logger.info("Starting import_feed with file: '%s' for client: %s", csv_path, client_id)
        records = self.csv_reader.read(csv_path)
        if not records:
            logger.info("No valid records found in feed CSV.")
            return
        logger.info("Parsed %d valid record(s) from CSV.", len(records))
        self._upsert_feed_records(records, client_id)

    def _upsert_feed_records(self, records: list, client_id: int):
        product_ids = tuple(record[0] for record in records)
        existing_ids = self.repository.get_existing_product_ids(client_id, product_ids)

        conn = db_connection.get_connection()
        updated_count = 0
        inserted_count = 0
        try:
            with conn.cursor() as cur:
                for record in records:
                    product_id = record[0]
                    if product_id in existing_ids:
                        self.repository.update_product(cur, client_id, record)
                        updated_count += 1
                    else:
                        self.repository.insert_product(cur, client_id, record)
            conn.commit()
            logger.info(
                "Synchronization summary for client %s: Updated %d record(s), Inserted %d new record(s).",
                client_id, updated_count, inserted_count
            )
        except Exception as e:
            logger.exception("Database error during feed import: %s", e)
            conn.rollback()
            raise
        finally:
            conn.close()
            logger.info("Database connection closed after feed import.")
