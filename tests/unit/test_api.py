import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import tempfile
import os

from app.main import app

client = TestClient(app)

class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure the /tmp directory exists (especially on Windows)
        os.makedirs('/tmp', exist_ok=True)

    @patch("db.connection.DatabaseConnection.get_connection")
    def test_list_products(self, mock_db_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock rows
        mock_cursor.fetchall.return_value = [
            (1, "Test Product", 12.34, 101)
        ]

        response = client.get("/products?client_id=1")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["product_id"], 1)
        self.assertEqual(data[0]["title"], "Test Product")

    @patch("db.connection.DatabaseConnection.get_connection")
    def test_import_feed(self, mock_db_conn):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = []

        csv_data = "product_id,title,price,store_id\n1,Test,99.99,101\n"

        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.csv') as temp:
            temp.write(csv_data)
            temp_name = temp.name

        try:
            with open(temp_name, "rb") as f:
                files = {"file": ("test_feed.csv", f, "text/csv")}
                response = client.post("/products/feed?client_id=1", files=files)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["message"], "Feed imported successfully.")
        finally:
            os.remove(temp_name)

if __name__ == "__main__":
    unittest.main()
