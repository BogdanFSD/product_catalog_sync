import csv
import logging
from db import get_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_feed_csv(csv_path: str, client_id: int):
    """
    Reads feed_items.csv, validates the rows, and inserts only new records
    into the products table. Existing records are left unchanged; the synchronizer
    will later handle any updates or deletions.
    """
    records = []

    # Read and validate CSV rows.
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    product_id = int(row["product_id"])
                    title = row["title"].strip()
                    price = float(row["price"])
                    store_id = int(row["store_id"])
                    records.append((product_id, title, price, store_id))
                except (ValueError, KeyError) as e:
                    logger.error(f"Skipping row due to error: {row} -- {e}")
    except Exception as e:
        logger.exception(f"Error reading CSV file {csv_path}: {e}")
        return

    if not records:
        logger.info("No valid records found in feed CSV.")
        return

    # Connect to the database and insert only new records.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Get the set of product_ids from the CSV.
            product_ids = tuple(record[0] for record in records)
            if not product_ids:
                logger.info("No product IDs found in CSV.")
                return

            # Retrieve existing product_ids for this client.
            query = """
                SELECT product_id
                FROM products
                WHERE client_id = %s AND product_id IN %s
            """
            cur.execute(query, (client_id, product_ids))
            existing_ids = {row[0] for row in cur.fetchall()}

            # Filter records to insert only those not already in the database.
            new_records = [record for record in records if record[0] not in existing_ids]

            if new_records:
                insert_sql = """
                    INSERT INTO products (client_id, product_id, title, price, store_id)
                    VALUES (%s, %s, %s, %s, %s)
                """
                for product_id, title, price, store_id in new_records:
                    cur.execute(insert_sql, (client_id, product_id, title, price, store_id))
                conn.commit()
                logger.info(f"Inserted {len(new_records)} new records for client {client_id}.")
            else:
                logger.info("No new records to insert.")
    except Exception as e:
        logger.exception("Database error during feed import: %s", e)
        conn.rollback()
    finally:
        conn.close()
