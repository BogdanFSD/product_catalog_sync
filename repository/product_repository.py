import logging
from db.connection import DatabaseConnection

logger = logging.getLogger(__name__)

db_connection = DatabaseConnection()

class ProductRepository:
    """
    Encapsulates all database operations for products.
    """

    def get_existing_product_ids(self, client_id: int, product_ids: tuple) -> set:
        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    SELECT product_id
                    FROM products
                    WHERE client_id = %s AND product_id IN %s
                """
                cur.execute(query, (client_id, product_ids))
                existing_ids = {row[0] for row in cur.fetchall()}
        return existing_ids

    def update_product(self, cur, client_id: int, record: tuple):
        product_id, title, price, store_id = record
        update_sql = """
            UPDATE products
            SET title = %s,
                price = %s,
                store_id = %s,
                updated_at = NOW()
            WHERE client_id = %s AND product_id = %s
        """
        cur.execute(update_sql, (title, price, store_id, client_id, product_id))
        logger.info("Updated product_id %s for client %s", product_id, client_id)

    def insert_product(self, cur, client_id: int, record: tuple):
        product_id, title, price, store_id = record
        insert_sql = """
            INSERT INTO products (client_id, product_id, title, price, store_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(insert_sql, (client_id, product_id, title, price, store_id))
        logger.info("Inserted product_id %s for client %s", product_id, client_id)
