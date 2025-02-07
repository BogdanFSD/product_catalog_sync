import unittest
import tempfile
import csv
import os
import sys
from db import get_connection
from models import create_tables
from main import main
from unittest.mock import patch

class TestMainIntegration(unittest.TestCase):
    def setUp(self):
        create_tables()
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE")
        conn.commit()
        conn.close()

    def test_main_with_feed_integration(self):
        # Make a temp feed CSV
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        writer = csv.writer(temp_csv)
        writer.writerow(["product_id", "title", "price", "store_id"])
        writer.writerow(["1", "Main Integration Product", "12.34", "101"])
        temp_csv.close()

        # Run main with real DB
        args = ["main.py", "--feed", temp_csv.name, "--client", "1"]
        with patch.object(sys, 'argv', args):
            main()

        # Verify
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, title, price FROM products WHERE client_id=1")
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 1)
        conn.close()

        os.unlink(temp_csv.name)
