import unittest
import logging
from services.table_creator import TableCreator

class NoCloseConnection:
    """
    A wrapper for a persistent connection that overrides the close() method
    and supports the context manager protocol.
    """
    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, attr):
        return getattr(self._conn, attr)

    def close(self):
       pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

class BaseIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reduce logging overhead during tests.
        logging.getLogger().setLevel(logging.WARNING)

        TableCreator().create_tables()
        from db.connection import DatabaseConnection as DBConn
        cls._persistent_conn = DBConn().get_connection()
        cls._persistent_conn.autocommit = False  # Ensure we are in transactional mode.

        cls._original_get_connection = DBConn.get_connection
        DBConn.get_connection = lambda self: NoCloseConnection(cls._persistent_conn)

    def setUp(self):
            cur = self._persistent_conn.cursor()
            cur.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE")
            self._persistent_conn.commit()
            cur.close()

    @classmethod
    def tearDownClass(cls):
        from db.connection import DatabaseConnection as DBConn
        DBConn.get_connection = cls._original_get_connection
        cls._persistent_conn.close()
