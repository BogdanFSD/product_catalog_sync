import unittest
from unittest.mock import mock_open, patch
from tests.base_mock_db import BaseMockDBTest

from services.feed_importer import FeedImporter, FeedCsvReader
from repository.product_repository import ProductRepository

class TestImporterUnit(BaseMockDBTest):
    def test_no_valid_records(self):
        # CSV with only headers -> no valid records
        csv_data = "product_id,title,price,store_id\n"
        with patch("builtins.open", mock_open(read_data=csv_data)):
            importer = FeedImporter(ProductRepository(), FeedCsvReader())
            importer.import_feed("dummy.csv", 1)
        self.fake_conn.commit.assert_not_called()

    def test_insert_branch(self):
        csv_data = "product_id,title,price,store_id\n1,Test Product,12.34,101\n"
        # Suppose no existing rows in DB
        self.fake_cursor.fetchall.return_value = []

        with patch("builtins.open", mock_open(read_data=csv_data)):
            importer = FeedImporter(ProductRepository(), FeedCsvReader())
            importer.import_feed("dummy.csv", 1)

        self.assertTrue(self.fake_conn.commit.called)
        insert_queries = [
            call for call in self.fake_cursor.execute.call_args_list
            if "INSERT INTO products" in call[0][0]
        ]
        self.assertGreaterEqual(len(insert_queries), 1, "Expected an INSERT")

if __name__ == '__main__':
    unittest.main()
