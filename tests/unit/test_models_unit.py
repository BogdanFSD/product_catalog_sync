import unittest
from unittest.mock import MagicMock, patch
from psycopg2 import DatabaseError
from models import create_tables
from tests.base_mock_db import BaseMockDBTest

class TestModelsUnit(BaseMockDBTest):
    def test_create_tables_success(self):
        """
        Test create_tables runs the SQL using the mocked connection/cursor.
        """
        create_tables()
        # self.fake_cursor.execute should have been called at least once
        self.fake_cursor.execute.assert_called()
        self.fake_conn.commit.assert_called_once()

    def test_create_tables_error(self):
        """
        Test create_tables triggers rollback on error.
        """
        self.fake_cursor.execute.side_effect = DatabaseError("Mock table creation error")
        create_tables()
        self.fake_conn.rollback.assert_called_once()
        self.fake_conn.close.assert_called_once()
