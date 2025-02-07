from db import get_connection

def create_tables():
    """
    Creates the products table if it doesn't exist.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        client_id INT NOT NULL,
        product_id INT NOT NULL,
        title VARCHAR(255) NOT NULL,
        price NUMERIC(10,2) NOT NULL,
        store_id INT NOT NULL,
        updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        UNIQUE (client_id, product_id)
    );
    """

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
        conn.commit()
    finally:
        conn.close()
