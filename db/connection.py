import os
import psycopg2
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Responsible for providing a database connection.
    """

    def __init__(self):
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")

    def get_connection(self):
        """
        Returns a new psycopg2 connection.
        """
        try:
            logger.info("Attempting to establish database connection...")
            conn = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            logger.info("Database connection established successfully.")
            return conn
        except Exception as e:
            logger.exception("Failed to establish database connection: %s", e)
            raise
