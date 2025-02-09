import unittest
from unittest.mock import patch, MagicMock
import psycopg2

from db.connection import DatabaseConnection

class TestDBUnit(unittest.TestCase):
    """
    Unit-level tests for db/connection.py using mocks.
    """

    def test_get_connection_failure(self):
        """
        Force psycopg2.connect to raise OperationalError and ensure exception is re-raised.
        """
        with patch("psycopg2.connect", side_effect=psycopg2.OperationalError("Mock connection error")):
            db_conn = DatabaseConnection()
            with self.assertRaises(psycopg2.OperationalError):
                db_conn.get_connection()

    def test_get_connection_success(self):
        """
        Check that we can get a connection if psycopg2.connect doesn't fail.
        """
        with patch("psycopg2.connect", return_value=MagicMock()) as mock_connect:
            db_conn = DatabaseConnection()
            conn = db_conn.get_connection()
            self.assertIsNotNone(conn)
            mock_connect.assert_called_once()
