import unittest
from db.connection import DatabaseConnection
from tests.integration.base_integration import BaseIntegrationTest

class TestDBIntegration(BaseIntegrationTest):
    def test_real_connection(self):
        db_conn = DatabaseConnection()
        conn = db_conn.get_connection()
        self.assertIsNotNone(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            self.assertEqual(result[0], 1)


if __name__ == '__main__':
    unittest.main()
