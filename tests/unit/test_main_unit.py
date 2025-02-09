import sys
import unittest
import runpy
from unittest.mock import patch, mock_open

from tests.helpers import fake_connection_factory
from cli import main

class TestMainUnit(unittest.TestCase):
    def test_main_feed_only(self):
        """
        If user passes only --feed, we create tables + import feed, but do NOT do portal sync.
        """
        test_args = ["cli.py", "--feed", "feed.csv", "--client", "1"]
        feed_csv_data = "product_id,title,price,store_id\n1,Test Product,9.99,100\n"

        with patch.object(sys, 'argv', test_args), \
             patch("builtins.open", mock_open(read_data=feed_csv_data)), \
             patch("psycopg2.connect", return_value=fake_connection_factory()) as mock_connect, \
             patch("services.portal_synchronizer.PortalSynchronizer") as mock_sync_class:
            main()

        # No portal => no PortalSynchronizer usage
        mock_sync_class.assert_not_called()

        self.assertEqual(
            mock_connect.call_count, 3,
            f"Expected 3 calls to psycopg2.connect, got {mock_connect.call_count}"
        )

    def test_main_feed_and_portal(self):
        """
        If user passes --feed AND --portal, we do both feed import and portal sync.
        We'll patch builtins.open with 2 side_effect data strings: feed + portal.
        """
        test_args = ["cli.py", "--feed", "feed.csv", "--portal", "portal.csv", "--client", "1"]
        feed_data = "product_id,title,price,store_id\n1,FeedProduct,12.34,101\n"
        portal_data = "product_id,title,price,store_id\n2,PortalProd,55.55,202\n"

        mo = mock_open()
        mo.side_effect = [
            mock_open(read_data=feed_data).return_value,
            mock_open(read_data=portal_data).return_value,
        ]

        with patch.object(sys, 'argv', test_args), \
             patch("builtins.open", mo), \
             patch("psycopg2.connect", return_value=fake_connection_factory()) as mock_connect:
            main()

        self.assertEqual(
            mock_connect.call_count, 5,
            f"Expected 5 calls to psycopg2.connect, got {mock_connect.call_count}"
        )

    def test_main_run_module(self):
        """
        Test running the main module with minimal arguments. 
        We'll patch psycopg2.connect so there's no real DB call, but let the code run.
        """
        test_args = ["cli.py", "--feed", "feed.csv", "--client", "1"]
        feed_csv_data = "product_id,title,price,store_id\n1,Dummy,0.0,0\n"

        with patch("builtins.open", mock_open(read_data=feed_csv_data)), \
             patch("psycopg2.connect", return_value=fake_connection_factory()) as mock_connect, \
             patch.object(sys, 'argv', test_args):
            runpy.run_module("cli", run_name="__main__")

        self.assertEqual(
            mock_connect.call_count, 3,
            f"Expected 3 calls to psycopg2.connect, got {mock_connect.call_count}"
        )

    def test_main_run_module_fakedb(self):
        """
        Variation of runpy test verifying we commit changes with a fake DB.
        """
        fake_conn = fake_connection_factory()
        feed_csv_data = "product_id,title,price,store_id\n1,Dummy,0.0,0\n"

        with patch("psycopg2.connect", return_value=fake_conn), \
             patch("builtins.open", mock_open(read_data=feed_csv_data)), \
             patch.object(sys, 'argv', ["cli.py", "--feed", "dummy_feed.csv", "--client", "1"]):
            runpy.run_module("cli", run_name="__main__")

        self.assertTrue(
            fake_conn.commit.called,
            "Expected commit() with a fake DB connection"
        )
