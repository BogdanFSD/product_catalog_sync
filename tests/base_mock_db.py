import unittest
from unittest.mock import patch
from tests.helpers import fake_connection_factory

class BaseMockDBTest(unittest.TestCase):
    """
    Base class for unit tests that need to mock out the DB connection.
    """
    def setUp(self):
        # Create a fake connection/cursor
        self.fake_conn = fake_connection_factory()
        self.fake_cursor = self.fake_conn.cursor.return_value.__enter__.return_value

        # Patch get_connection so that any calls to importer.get_connection or synchronizer.get_connection
        # will return our fake_conn. 
        # For a single source of truth, do it *once per module that calls get_connection*:
        patcher_importer = patch("importer.get_connection", return_value=self.fake_conn)
        patcher_sync = patch("synchronizer.get_connection", return_value=self.fake_conn)
        patcher_db_in_models = patch("models.get_connection", return_value=self.fake_conn)
        # If your main calls get_connection directly, patch that as well:
        # patcher_main = patch("main.get_connection", return_value=self.fake_conn)

        # Start them
        self.mock_importer_conn = patcher_importer.start()
        self.mock_sync_conn = patcher_sync.start()
        self.mock_models_conn = patcher_db_in_models.start()
        # self.mock_main_conn = patcher_main.start()

        self.addCleanup(patcher_importer.stop)
        self.addCleanup(patcher_sync.stop)
        self.addCleanup(patcher_db_in_models.stop)
        # self.addCleanup(patcher_main.stop)

        # Reset commit/rollback for each test
        self.fake_conn.commit.reset_mock()
        self.fake_conn.rollback.reset_mock()
