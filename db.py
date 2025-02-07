import os
import psycopg2
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

def get_connection():
    """
    Returns a new psycopg2 connection.
    Edit environment variables or default to local DB.
    """
    try:
        logger.info("Attempting to establish database connection...")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")

        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        logger.info("Database connection established successfully.")
        return conn
    except Exception as e:
        logger.exception("Failed to establish database connection: %s", e)
        raise
