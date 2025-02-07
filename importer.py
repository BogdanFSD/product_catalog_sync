import csv
import logging
from db import get_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_feed_csv(csv_path: str, client_id: int):
    """
    Reads feed_items.csv, validates the rows, and updates existing records or inserts new ones
    into the products table. If a product (identified by client_id and product_id) exists,
    it is updated with the new title, price, and store_id (and updated_at is set to NOW()).
    Otherwise, the product is inserted.
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

    # Connect to the database and update or insert records accordingly.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Get all product_ids from the CSV.
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

            updated_count = 0
            inserted_count = 0

            for product_id, title, price, store_id in records:
                if product_id in existing_ids:
                    # Update the existing record.
                    update_sql = """
                        UPDATE products
                        SET title = %s,
                            price = %s,
                            store_id = %s,
                            updated_at = NOW()
                        WHERE client_id = %s AND product_id = %s
                    """
                    cur.execute(update_sql, (title, price, store_id, client_id, product_id))
                    updated_count += 1
                else:
                    # Insert a new record.
                    insert_sql = """
                        INSERT INTO products (client_id, product_id, title, price, store_id)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cur.execute(insert_sql, (client_id, product_id, title, price, store_id))
                    inserted_count += 1

            conn.commit()
            logger.info(f"Updated {updated_count} records, Inserted {inserted_count} new records for client {client_id}.")
    except Exception as e:
        logger.exception("Database error during feed import: %s", e)
        conn.rollback()
    finally:
        conn.close()
