import sys
import unittest
import runpy
from io import StringIO
from unittest.mock import patch, mock_open

from tests.helpers import fake_connection_factory
from main import main

class TestMainUnit(unittest.TestCase):
    def test_main_feed_only(self):
        test_args = ["main.py", "--feed", "feed.csv", "--client", "1"]
        with patch.object(sys, 'argv', test_args), \
             patch("main.create_tables") as mock_create, \
             patch("main.import_feed_csv") as mock_feed, \
             patch("main.synchronize_portal") as mock_sync:
            main()
        mock_create.assert_called_once()
        mock_feed.assert_called_once_with("feed.csv", 1)
        mock_sync.assert_not_called()

    def test_main_feed_and_portal(self):
        test_args = ["main.py", "--feed", "feed.csv", "--portal", "portal.csv", "--client", "1"]
        with patch.object(sys, 'argv', test_args), \
             patch("main.create_tables") as mock_create, \
             patch("main.import_feed_csv") as mock_feed, \
             patch("main.synchronize_portal") as mock_sync:
            main()
        mock_create.assert_called_once()
        mock_feed.assert_called_once_with("feed.csv", 1)
        mock_sync.assert_called_once_with("portal.csv", 1)

    def test_main_run_module(self):
        # This test uses runpy to execute main.
        # We'll patch open() and psycopg2.connect so that no real file I/O or DB connection is made.
        test_args = ["main.py", "--feed", "feed.csv", "--client", "1"]
        dummy_csv_data = "product_id,title,price,store_id\n1,Dummy,0.0,0\n"
        with patch("builtins.open", mock_open(read_data=dummy_csv_data)), \
             patch("psycopg2.connect", return_value=fake_connection_factory()) as mock_connect, \
             patch.object(sys, 'argv', test_args):
            runpy.run_module("main", run_name="__main__")
        # Because create_tables() and import_feed_csv() each call get_connection(),
        # psycopg2.connect is expected to be called twice.
        self.assertEqual(mock_connect.call_count, 2,
                         f"Expected psycopg2.connect to be called 2 times, got {mock_connect.call_count}")

    def test_main_run_module_fakedb(self):
        # This test is similar to the previous one; it ensures that a fake DB is used.
        fake_conn = fake_connection_factory()
        with patch("psycopg2.connect", return_value=fake_conn), \
             patch("builtins.open", mock_open(read_data="product_id,title,price,store_id\n1,Dummy,0.0,0\n")), \
             patch.object(sys, 'argv', ["main.py", "--feed", "dummy_feed.csv", "--client", "1"]):
            runpy.run_module("main", run_name="__main__")
        self.assertTrue(fake_conn.commit.called, "Expected commit() to be called when using a fake DB connection")

if __name__ == '__main__':
    unittest.main()
