import unittest
import tempfile
import csv
from db import get_connection
from models import create_tables
from synchronizer import synchronize_portal

class TestSynchronizerIntegration(unittest.TestCase):
    def setUp(self):
        create_tables()
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE")
        conn.commit()
        conn.close()

    def test_synchronize_portal_integration(self):
        # Insert some product
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO products (client_id, product_id, title, price, store_id) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (1, 1, "Old Title", 10.00, 101))
        conn.commit()
        conn.close()

        # Create a portal CSV to update product_id=1 and add product_id=2
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        writer = csv.writer(temp_csv)
        writer.writerow(["product_id", "title", "price", "store_id"])
        writer.writerow(["1", "New Title", "11.00", "101"])
        writer.writerow(["2", "New Product", "20.00", "102"])
        temp_csv.close()

        synchronize_portal(temp_csv.name, 1)

        # Check DB
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, title, price FROM products WHERE client_id=1 ORDER BY product_id")
            rows = cur.fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0], (1, "New Title", 11.00))
            self.assertEqual(rows[1], (2, "New Product", 20.00))
        conn.close()
