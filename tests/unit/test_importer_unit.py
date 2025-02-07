import unittest
from unittest.mock import mock_open, patch
from importer import import_feed_csv
from tests.base_mock_db import BaseMockDBTest

class TestImporterUnit(BaseMockDBTest):
    def test_no_valid_records(self):
        csv_data = "product_id,title,price,store_id\n"  # Only headers
        with patch("builtins.open", mock_open(read_data=csv_data)):
            import_feed_csv("dummy.csv", 1)
        self.fake_conn.commit.assert_not_called()

    def test_insert_branch(self):
        csv_data = "product_id,title,price,store_id\n1,Test Product,12.34,101\n"
        # Suppose no existing rows
        self.fake_cursor.fetchall.return_value = []

        with patch("builtins.open", mock_open(read_data=csv_data)):
            import_feed_csv("dummy.csv", 1)

        self.assertTrue(self.fake_conn.commit.called)
        insert_queries = [call for call in self.fake_cursor.execute.call_args_list
                          if "INSERT INTO products" in call[0][0]]
        self.assertTrue(len(insert_queries) >= 1, "Expected an INSERT")

    # ... other coverage tests, e.g. update branch, db exception, invalid rows ...
