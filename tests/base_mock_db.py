import unittest
from unittest.mock import patch
from tests.helpers import fake_connection_factory

class BaseMockDBTest(unittest.TestCase):
    """
    Base class for unit tests that need to mock out the DB connection.
    """
    def setUp(self):
        self.fake_conn = fake_connection_factory()
        self.fake_cursor = self.fake_conn.cursor.return_value.__enter__.return_value

        # Patch the db_connection.get_connection() calls in relevant service modules
        patcher_importer = patch(
            "services.feed_importer.db_connection.get_connection",
            return_value=self.fake_conn
        )
        patcher_sync = patch(
            "services.portal_synchronizer.db_connection.get_connection",
            return_value=self.fake_conn
        )
        patcher_table_creator = patch(
            "services.table_creator.db_connection.get_connection",
            return_value=self.fake_conn
        )

        self.mock_importer_conn = patcher_importer.start()
        self.mock_sync_conn = patcher_sync.start()
        self.mock_table_creator_conn = patcher_table_creator.start()

        self.addCleanup(patcher_importer.stop)
        self.addCleanup(patcher_sync.stop)
        self.addCleanup(patcher_table_creator.stop)

        self.fake_conn.commit.reset_mock()
        self.fake_conn.rollback.reset_mock()
