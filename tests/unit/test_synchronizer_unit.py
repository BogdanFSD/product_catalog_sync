import unittest
from unittest.mock import mock_open, patch
from tests.base_mock_db import BaseMockDBTest

from services.portal_synchronizer import PortalSynchronizer


class TestSynchronizerUnit(BaseMockDBTest):
    def test_no_valid_records(self):
        csv_data = "product_id,title,price,store_id\n"
        with patch("builtins.open", mock_open(read_data=csv_data)):
            sync = PortalSynchronizer()
            records = sync.read_portal_csv("dummy.csv")
            self.assertEqual(records, {}, "Expected no valid portal records found")
        self.fake_conn.commit.assert_not_called()

    def test_success_branches(self):
        """
        We want DB to contain product 1 and product 2
        while the portal CSV contains product 1 and product 3.
        Then compute_sync_actions should return:
         - to_delete = {2}
         - to_insert = {3: ...}
         - to_update = {1: ...} (because product 1’s data is different)
        """
        csv_data = (
            "product_id,title,price,store_id\n"
            "1,Portal Updated,99.99,101\n"
            "3,New Portal,49.99,103\n"
        )
        # Expected fake DB records: product 1 and product 2.
        expected_db_records = [
            (1, "Old Product", 50.00, 101),
            (2, "To Delete", 30.00, 102)
        ]
        # Set the fake cursor's fetchall to return expected_db_records
        self.fake_cursor.fetchall.return_value = expected_db_records


        with patch("builtins.open", mock_open(read_data=csv_data)):
            sync = PortalSynchronizer()
            portal_records = sync.read_portal_csv("dummy.csv")

            db_products = {1: {'title': 'Old Product', 'price': 50.0, 'store_id': 101},
                           2: {'title': 'To Delete', 'price': 30.0, 'store_id': 102}}

            to_delete, to_insert, to_update = sync.compute_sync_actions(db_products, portal_records)


            self.assertEqual(to_delete, {2}, "Expected to delete product 2")
            self.assertEqual(set(to_insert.keys()), {3}, "Expected to insert product 3")
            self.assertEqual(set(to_update.keys()), {1}, "Expected to update product 1")

            sync.apply_sync_actions(1, to_delete, to_insert, to_update)

        delete_calls = [
            c for c in self.fake_cursor.execute.call_args_list
            if "DELETE FROM products" in c[0][0] and c[0][1] == (1, 2)
        ]
        insert_calls = [
            c for c in self.fake_cursor.execute.call_args_list
            if "INSERT INTO products" in c[0][0] and c[0][1][1] == 3
        ]
        update_calls = [
            c for c in self.fake_cursor.execute.call_args_list
            if "UPDATE products" in c[0][0] and c[0][1][-1] == 1
        ]

        self.assertTrue(delete_calls, "Should have at least one DELETE for product_id=2")
        self.assertTrue(insert_calls, "Should have at least one INSERT for product_id=3")
        self.assertTrue(update_calls, "Should have at least one UPDATE for product_id=1")
        self.assertTrue(self.fake_conn.commit.called)


if __name__ == '__main__':
    unittest.main()
