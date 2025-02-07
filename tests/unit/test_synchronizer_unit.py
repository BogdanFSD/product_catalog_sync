import unittest
from unittest.mock import mock_open, patch
from synchronizer import synchronize_portal
from tests.base_mock_db import BaseMockDBTest

class TestSynchronizerUnit(BaseMockDBTest):
    def test_no_valid_records(self):
        csv_data = "product_id,title,price,store_id\n"
        with patch("builtins.open", mock_open(read_data=csv_data)):
            synchronize_portal("dummy.csv", 1)
        self.fake_conn.commit.assert_not_called()

    def test_success_branches(self):
        csv_data = (
            "product_id,title,price,store_id\n"
            "1,Portal Updated,99.99,101\n"
            "3,New Portal,49.99,103\n"
        )
        # Fake existing DB records: product_id=1, product_id=2
        self.fake_cursor.fetchall.return_value = [
            (1, "Old Product", 50.00, 101),
            (2, "To Delete", 30.00, 102)
        ]

        with patch("builtins.open", mock_open(read_data=csv_data)):
            synchronize_portal("dummy.csv", 1)

        delete_calls = [c for c in self.fake_cursor.execute.call_args_list if "DELETE FROM products" in c[0][0]]
        insert_calls = [c for c in self.fake_cursor.execute.call_args_list if "INSERT INTO products" in c[0][0]]
        update_calls = [c for c in self.fake_cursor.execute.call_args_list if "UPDATE products" in c[0][0]]
        self.assertTrue(delete_calls, "Should have at least one DELETE")
        self.assertTrue(insert_calls, "Should have at least one INSERT")
        self.assertTrue(update_calls, "Should have at least one UPDATE")
        self.assertTrue(self.fake_conn.commit.called)
