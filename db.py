import os
import psycopg2

def get_connection():
    """
    Returns a new psycopg2 connection.
    Edit environment variables or default to local DB.
    """
    db_name = os.getenv("DB_NAME",)
    db_user = os.getenv("DB_USER",)
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
    return conn
