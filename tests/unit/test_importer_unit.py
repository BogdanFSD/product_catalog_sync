import unittest
from unittest.mock import mock_open, patch
from tests.base_mock_db import BaseMockDBTest

from services.feed_importer import FeedImporter, FeedCsvReader
from repository.product_repository import ProductRepository

class TestImporterUnit(BaseMockDBTest):
    def test_no_valid_records(self):
        csv_data = "product_id,title,price,store_id\n"
        with patch("builtins.open", mock_open(read_data=csv_data)):
            importer = FeedImporter(ProductRepository(), FeedCsvReader())
            importer.import_feed("dummy.csv", 1)
        self.fake_conn.commit.assert_not_called()

if __name__ == '__main__':
    unittest.main()
