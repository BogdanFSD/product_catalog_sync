import unittest
import tempfile
import csv
import os
import sys
from db.connection import DatabaseConnection
from tests.integration.base_integration import BaseIntegrationTest
from cli import main
from unittest.mock import patch

class TestMainIntegration(BaseIntegrationTest):
    def test_main_with_feed_integration(self):

        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        writer = csv.writer(temp_csv)
        writer.writerow(["product_id", "title", "price", "store_id"])
        writer.writerow(["1", "Main Integration Product", "12.34", "101"])
        temp_csv.close()

        args = ["main.py", "--feed", temp_csv.name, "--client", "1"]
        with patch.object(sys, 'argv', args):
            main()

        conn = DatabaseConnection().get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, title, price FROM products WHERE client_id = %s", (1,))
            row = cur.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 1)
        os.unlink(temp_csv.name)

if __name__ == '__main__':
    unittest.main()
