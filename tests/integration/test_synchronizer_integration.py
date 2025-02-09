import unittest
import tempfile
import csv
import os
from db.connection import DatabaseConnection
from tests.integration.base_integration import BaseIntegrationTest
from services.portal_synchronizer import PortalSynchronizer

class TestSynchronizerIntegration(BaseIntegrationTest):
    def test_synchronize_portal_integration(self):
        # Insert an initial product record to update.
        conn = DatabaseConnection().get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO products (client_id, product_id, title, price, store_id) VALUES (%s, %s, %s, %s, %s)",
                (1, 1, "Old Title", 10.00, 101)
            )
        conn.commit()

        # Create a temporary CSV file that updates product 1 and adds product 2.
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        writer = csv.writer(temp_csv)
        writer.writerow(["product_id", "title", "price", "store_id"])
        writer.writerow(["1", "New Title", "11.00", "101"])
        writer.writerow(["2", "New Product", "20.00", "102"])
        temp_csv.close()

        sync = PortalSynchronizer()
        portal_records = sync.read_portal_csv(temp_csv.name)
        db_products = sync.fetch_db_products(1)
        to_delete, to_insert, to_update = sync.compute_sync_actions(db_products, portal_records)
        sync.apply_sync_actions(1, to_delete, to_insert, to_update)

        # Verify changes in the database.
        conn = DatabaseConnection().get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT product_id, title, price FROM products WHERE client_id = %s ORDER BY product_id", (1,))
            rows = cur.fetchall()
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0][0], 1)
            self.assertEqual(rows[0][1], "New Title")
            self.assertAlmostEqual(float(rows[0][2]), 11.00, places=2)
            self.assertEqual(rows[1][0], 2)
            self.assertEqual(rows[1][1], "New Product")
            self.assertAlmostEqual(float(rows[1][2]), 20.00, places=2)
        os.unlink(temp_csv.name)

if __name__ == '__main__':
    unittest.main()
