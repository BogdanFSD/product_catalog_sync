import unittest
from db import get_connection
from models import create_tables

class TestModelsIntegration(unittest.TestCase):
    def setUp(self):
        create_tables()
        # Optionally TRUNCATE TABLE here if you want a clean slate each time
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE")
        conn.commit()
        conn.close()

    def test_create_tables_already_exists(self):
        """
        Just call create_tables again to ensure it doesn't fail if table already exists.
        """
        create_tables()  # Shouldn't raise an exception
