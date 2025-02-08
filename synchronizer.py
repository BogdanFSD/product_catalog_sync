import csv
import logging
from db import get_connection

logger = logging.getLogger(__name__)

def read_portal_csv(csv_path: str) -> dict:
    """
    Reads the portal CSV file and returns a dictionary mapping product_id to record data.
    Each record is a dict with keys: 'title', 'price', 'store_id'.
    """
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

def fetch_db_products(client_id: int) -> dict:
    """
    Retrieves current products from the database for the given client_id.
    Returns a dictionary mapping product_id to a record with keys: 'title', 'price', 'store_id'.
    """
    db_products = {}
    try:
        with get_connection() as conn:
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

def compute_sync_actions(db_products: dict, portal_records: dict) -> tuple:
    """
    Compares the database products and the portal records to compute:
      - Deletions: product IDs to delete (present in DB but not in portal).
      - Insertions: records to insert (present in portal but not in DB).
      - Updates: records to update (present in both, but with differing data).
    Returns a tuple (to_delete, to_insert, to_update) where:
      - to_delete is a set of product_ids.
      - to_insert is a dict mapping product_id to record data.
      - to_update is a dict mapping product_id to record data.
    """
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

def apply_sync_actions(client_id: int, to_delete: set, to_insert: dict, to_update: dict):
    """
    Applies the synchronization actions to the database:
      - Deletes products listed in to_delete.
      - Inserts new products from to_insert.
      - Updates existing products from to_update.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Process deletions
            for pid in to_delete:
                cur.execute(
                    "DELETE FROM products WHERE client_id = %s AND product_id = %s",
                    (client_id, pid)
                )
                logger.info("Deleted product_id %s for client %s", pid, client_id)

            # Process insertions
            for pid, record in to_insert.items():
                cur.execute(
                    "INSERT INTO products (client_id, product_id, title, price, store_id) VALUES (%s, %s, %s, %s, %s)",
                    (client_id, pid, record["title"], record["price"], record["store_id"])
                )
                logger.info("Inserted product_id %s for client %s", pid, client_id)

            # Process updates
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

def synchronize_portal(portal_csv_path: str, client_id: int):
    """
    High-level function that synchronizes the database with the portal CSV.
    Steps:
      1. Reads the portal CSV file.
      2. Retrieves current products from the database.
      3. Computes the required actions (deletions, insertions, updates).
      4. Applies these actions.
    """
    logger.info("Starting portal synchronization for client %s using file: '%s'", client_id, portal_csv_path)
    
    # 1. Read the portal CSV.
    portal_records = read_portal_csv(portal_csv_path)
    if not portal_records:
        logger.info("No valid portal records found in CSV.")
        return

    # 2. Fetch current products from the database.
    db_products = fetch_db_products(client_id)

    # 3. Compute which actions to take.
    to_delete, to_insert, to_update = compute_sync_actions(db_products, portal_records)

    # 4. Apply the computed actions.
    apply_sync_actions(client_id, to_delete, to_insert, to_update)
