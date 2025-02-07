import csv
import logging
from db import get_connection

# Configure logging (if not already configured in main)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_feed_csv(csv_path: str, client_id: int):
    """
    Reads feed_items.csv, validates the rows, and updates existing records or inserts new ones
    into the products table. If a product (identified by client_id and product_id) exists,
    it is updated with the new title, price, and store_id (and updated_at is set to NOW()).
    Otherwise, the product is inserted.
    """
    logger.info("Starting import_feed_csv with file: '%s' for client: %s", csv_path, client_id)
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
                    logger.error("Skipping row due to error: %s -- %s", row, e)
    except Exception as e:
        logger.exception("Error reading CSV file '%s': %s", csv_path, e)
        return

    if not records:
        logger.info("No valid records found in feed CSV.")
        return

    logger.info("Parsed %d valid record(s) from CSV.", len(records))

    # Connect to the database and update or insert records accordingly.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Get all product_ids from the CSV.
            product_ids = tuple(record[0] for record in records)
            if not product_ids:
                logger.info("No product IDs found in CSV.")
                return

            logger.info("Retrieving existing product IDs for client %s", client_id)
            query = """
                SELECT product_id
                FROM products
                WHERE client_id = %s AND product_id IN %s
            """
            cur.execute(query, (client_id, product_ids))
            existing_ids = {row[0] for row in cur.fetchall()}
            logger.info("Found %d existing product(s) for client %s", len(existing_ids), client_id)

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
                    logger.info("Updated product_id %s for client %s", product_id, client_id)
                else:
                    # Insert a new record.
                    insert_sql = """
                        INSERT INTO products (client_id, product_id, title, price, store_id)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cur.execute(insert_sql, (client_id, product_id, title, price, store_id))
                    inserted_count += 1
                    logger.info("Inserted product_id %s for client %s", product_id, client_id)

            conn.commit()
            logger.info("Database commit successful.")
            logger.info("Synchronization summary for client %s: Updated %d record(s), Inserted %d new record(s).", 
                        client_id, updated_count, inserted_count)
    except Exception as e:
        logger.exception("Database error during feed import: %s", e)
        conn.rollback()
    finally:
        conn.close()
        logger.info("Database connection closed after feed import.")
