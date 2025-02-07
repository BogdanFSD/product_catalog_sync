import unittest
from unittest.mock import patch, MagicMock
import psycopg2
from db import get_connection

class TestDBUnit(unittest.TestCase):
    """
    Unit-level tests for db.py, using mocks
    """

    def test_get_connection_failure(self):
        """
        Force psycopg2.connect to raise OperationalError, ensure exception is re-raised.
        """
        with patch("psycopg2.connect", side_effect=psycopg2.OperationalError("Mock connection error")):
            with self.assertRaises(psycopg2.OperationalError):
                get_connection()

    def test_get_connection_success(self):
        """
        Check that we can get a connection if psycopg2.connect doesn't fail.
        """
        with patch("psycopg2.connect", return_value=MagicMock()) as mock_connect:
            conn = get_connection()
            self.assertIsNotNone(conn)
            mock_connect.assert_called_once()
