import csv
import logging

logger = logging.getLogger(__name__)

class FeedCsvReader:
    """
    Responsible for reading and validating feed CSV files.
    """

    def read(self, csv_path: str) -> list:
        """
        Reads the CSV file at csv_path and returns a list of valid records.
        Each record is a tuple: (product_id, title, price, store_id).
        Invalid rows are skipped and an error is logged.
        """
        records = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        product_id = int(row["product_id"])
                        title = row["title"].strip()
                        price = float(row["price"])
                        store_id = int(row["store_id"])
                        records.append((product_id, title, price, store_id))
                    except (ValueError, KeyError) as e:
                        logger.error("Skipping row due to error: %s -- %s", row, e)
        except Exception as e:
            logger.exception("Error reading CSV file '%s': %s", csv_path, e)
            raise
        return records
