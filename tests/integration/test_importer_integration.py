import unittest
import os
import tempfile
import csv
from db import get_connection
from models import create_tables
from importer import import_feed_csv

class TestImporterIntegration(unittest.TestCase):
    def setUp(self):
        create_tables()
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE")
        conn.commit()
        conn.close()

    def test_import_feed_csv_integration(self):
        # Write a temp CSV
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        writer = csv.writer(temp_csv)
        writer.writerow(["product_id", "title", "price", "store_id"])
        writer.writerow(["1", "Integration Product", "9.99", "101"])
        temp_csv.close()

        import_feed_csv(temp_csv.name, 1)

        # Verify DB
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, title, price, store_id FROM products WHERE client_id=1")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 1)
        conn.close()

        os.unlink(temp_csv.name)
