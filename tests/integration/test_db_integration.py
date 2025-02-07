import unittest
from db import get_connection

class TestDBIntegration(unittest.TestCase):
    """
    Integration test that uses a real database connection.
    Make sure you have a test DB accessible via environment variables.
    """
    def test_real_connection(self):
        conn = get_connection()
        self.assertIsNotNone(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            self.assertEqual(result[0], 1)
        conn.close()
