import csv
import logging
from db import get_connection

logger = logging.getLogger(__name__)

def synchronize_portal(portal_csv_path: str, client_id: int):
    """
    Synchronizes the database with the portal CSV.
    - Deletions: Remove products from DB that are not in the portal CSV.
    - Updates: Update products in DB if their data has changed.
    - Insertions: Insert products from the portal CSV that are not in the DB.
    """
    logger.info("Starting portal synchronization for client %s using file: '%s'", client_id, portal_csv_path)
    portal_records = {}

    # Read and validate CSV rows.
    try:
        with open(portal_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    product_id = int(row["product_id"])
                    title = row["title"].strip()
                    price = float(row["price"])
                    store_id = int(row["store_id"])
                    portal_records[product_id] = {
                        "title": title,
                        "price": price,
                        "store_id": store_id
                    }
                except (ValueError, KeyError) as e:
                    logger.error("Skipping portal row due to error: %s -- %s", row, e)
    except Exception as e:
        logger.exception("Error reading portal CSV file '%s': %s", portal_csv_path, e)
        return

    if not portal_records:
        logger.info("No valid portal records found in CSV.")
        return

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Retrieve current products from DB for the client.
            logger.info("Retrieving current products from database for client %s", client_id)
            cur.execute("SELECT product_id, title, price, store_id FROM products WHERE client_id = %s", (client_id,))
            db_products = {row[0]: {"title": row[1], "price": float(row[2]), "store_id": row[3]} for row in cur.fetchall()}
            logger.info("Retrieved %d product(s) from the database.", len(db_products))

            # Determine deletions: products in DB but not in portal CSV.
            db_product_ids = set(db_products.keys())
            portal_product_ids = set(portal_records.keys())
            to_delete = db_product_ids - portal_product_ids

            # Determine insertions: products in portal CSV but not in DB.
            to_insert = portal_product_ids - db_product_ids

            # Determine potential updates: products in both.
            potential_updates = db_product_ids & portal_product_ids

            updated_count = 0
            inserted_count = 0
            deleted_count = 0

            # Handle deletions.
            for product_id in to_delete:
                cur.execute("DELETE FROM products WHERE client_id = %s AND product_id = %s", (client_id, product_id))
                deleted_count += 1
                logger.info("Deleted product_id %s for client %s", product_id, client_id)

            # Handle insertions.
            for product_id in to_insert:
                record = portal_records[product_id]
                cur.execute(
                    "INSERT INTO products (client_id, product_id, title, price, store_id) VALUES (%s, %s, %s, %s, %s)",
                    (client_id, product_id, record["title"], record["price"], record["store_id"])
                )
                inserted_count += 1
                logger.info("Inserted new product_id %s for client %s", product_id, client_id)

            # Handle updates.
            for product_id in potential_updates:
                portal_record = portal_records[product_id]
                db_record = db_products[product_id]
                if (portal_record["title"] != db_record["title"] or 
                    portal_record["price"] != db_record["price"] or 
                    portal_record["store_id"] != db_record["store_id"]):
                    cur.execute("""
                        UPDATE products
                        SET title = %s,
                            price = %s,
                            store_id = %s,
                            updated_at = NOW()
                        WHERE client_id = %s AND product_id = %s
                    """, (portal_record["title"], portal_record["price"], portal_record["store_id"], client_id, product_id))
                    updated_count += 1
                    logger.info("Updated product_id %s for client %s", product_id, client_id)

            conn.commit()
            logger.info("Portal synchronization commit successful.")
            logger.info("Synchronization summary for client %s: %d deleted, %d updated, %d inserted.", 
                        client_id, deleted_count, updated_count, inserted_count)
    except Exception as e:
        logger.exception("Database error during portal synchronization: %s", e)
        conn.rollback()
    finally:
        conn.close()
        logger.info("Database connection closed after portal synchronization.")
