import unittest
import os
import tempfile
import csv
from db.connection import DatabaseConnection
from repository.product_repository import ProductRepository
from services.csv_reader import FeedCsvReader
from services.feed_importer import FeedImporter
from tests.integration.base_integration import BaseIntegrationTest

class TestImporterIntegration(BaseIntegrationTest):
    def test_import_feed_csv_integration(self):
        # Create a temporary CSV file for feed import.
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        writer = csv.writer(temp_csv)
        writer.writerow(["product_id", "title", "price", "store_id"])
        writer.writerow(["1", "Integration Product", "9.99", "101"])
        temp_csv.close()

        importer = FeedImporter(ProductRepository(), FeedCsvReader())
        importer.import_feed(temp_csv.name, 1)

        db_conn = DatabaseConnection()
        conn = db_conn.get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, title, price, store_id FROM products WHERE client_id = %s", (1,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 1)

        os.unlink(temp_csv.name)

if __name__ == '__main__':
    unittest.main()
