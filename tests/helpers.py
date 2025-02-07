from unittest.mock import MagicMock

def fake_connection_factory():
    """
    Returns a MagicMock that simulates a psycopg2 connection object
    with a nested cursor.
    """
    fake_conn = MagicMock(name="fake_conn")
    fake_cursor = MagicMock(name="fake_cursor")

    # simulate usage of `with conn.cursor() as cur:`...
    fake_conn.cursor.return_value.__enter__.return_value = fake_cursor
    fake_conn.cursor.return_value.__exit__.return_value = False

    return fake_conn
