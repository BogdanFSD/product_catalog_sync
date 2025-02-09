import unittest
from unittest.mock import MagicMock
from psycopg2 import DatabaseError
from tests.base_mock_db import BaseMockDBTest

from services.table_creator import TableCreator

class TestModelsUnit(BaseMockDBTest):
    def test_create_tables_success(self):
        table_creator = TableCreator()
        table_creator.create_tables()

        self.fake_cursor.execute.assert_called()
        self.fake_conn.commit.assert_called_once()

    def test_create_tables_error(self):
        self.fake_cursor.execute.side_effect = DatabaseError("Mock table creation error")
        table_creator = TableCreator()
        table_creator.create_tables()

        self.fake_conn.rollback.assert_called_once()
        self.fake_conn.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()