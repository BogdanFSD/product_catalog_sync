import csv
import logging
from db.connection import DatabaseConnection

logger = logging.getLogger(__name__)

db_connection = DatabaseConnection()

class PortalSynchronizer:
    """
    Handles reading the portal CSV and synchronizing it with the DB state.
    """

    def read_portal_csv(self, csv_path: str) -> dict:
        records = {}
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        product_id = int(row["product_id"])
                        title = row["title"].strip()
                        price = float(row["price"])
                        store_id = int(row["store_id"])
                        records[product_id] = {
                            "title": title,
                            "price": price,
                            "store_id": store_id
                        }
                    except (ValueError, KeyError) as e:
                        logger.error("Skipping portal row due to error: %s -- %s", row, e)
        except Exception as e:
            logger.exception("Error reading portal CSV file '%s': %s", csv_path, e)
            raise e
        return records

    def fetch_db_products(self, client_id: int) -> dict:
        db_products = {}
        try:
            with db_connection.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT product_id, title, price, store_id FROM products WHERE client_id = %s",
                        (client_id,)
                    )
                    for row in cur.fetchall():
                        product_id, title, price, store_id = row
                        db_products[product_id] = {
                            "title": title,
                            "price": float(price),
                            "store_id": store_id
                        }
        except Exception as e:
            logger.exception("Error fetching DB products for client %s: %s", client_id, e)
            raise e
        return db_products

    def compute_sync_actions(self, db_products: dict, portal_records: dict) -> tuple:
        db_ids = set(db_products.keys())
        portal_ids = set(portal_records.keys())

        to_delete = db_ids - portal_ids
        to_insert = {pid: portal_records[pid] for pid in (portal_ids - db_ids)}

        to_update = {}
        for pid in db_ids & portal_ids:
            db_rec = db_products[pid]
            portal_rec = portal_records[pid]
            if (db_rec["title"] != portal_rec["title"] or
                db_rec["price"] != portal_rec["price"] or
                db_rec["store_id"] != portal_rec["store_id"]):
                to_update[pid] = portal_rec

        return to_delete, to_insert, to_update

    def apply_sync_actions(self, client_id: int, to_delete: set, to_insert: dict, to_update: dict):
        conn = db_connection.get_connection()
        try:
            with conn.cursor() as cur:
                # Deletions
                for pid in to_delete:
                    cur.execute(
                        "DELETE FROM products WHERE client_id = %s AND product_id = %s",
                        (client_id, pid)
                    )
                    logger.info("Deleted product_id %s for client %s", pid, client_id)

                # Insertions
                for pid, record in to_insert.items():
                    cur.execute(
                        """
                        INSERT INTO products (client_id, product_id, title, price, store_id)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (client_id, pid, record["title"], record["price"], record["store_id"])
                    )
                    logger.info("Inserted product_id %s for client %s", pid, client_id)

                # Updates
                for pid, record in to_update.items():
                    cur.execute(
                        """
                        UPDATE products
                        SET title = %s,
                            price = %s,
                            store_id = %s,
                            updated_at = NOW()
                        WHERE client_id = %s AND product_id = %s
                        """,
                        (record["title"], record["price"], record["store_id"], client_id, pid)
                    )
                    logger.info("Updated product_id %s for client %s", pid, client_id)

            conn.commit()
            logger.info(
                "Synchronization actions applied for client %s: deleted %d, inserted %d, updated %d.",
                client_id, len(to_delete), len(to_insert), len(to_update)
            )
        except Exception as e:
            logger.exception("Error applying sync actions for client %s: %s", client_id, e)
            conn.rollback()
            raise e
        finally:
            conn.close()
            logger.info("Database connection closed after applying sync actions.")
