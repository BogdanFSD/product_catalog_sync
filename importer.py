import csv
import logging
from db import get_connection

logger = logging.getLogger(__name__)

def read_feed_csv(csv_path: str) -> list:
    """
    Reads the CSV file at csv_path and returns a list of valid records.
    Each record is a tuple: (product_id, title, price, store_id).
    If a row is invalid, it is skipped with an error logged.
    """
    records = []
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
        raise e  # Re-raise so calling functions are aware
    return records

def get_existing_product_ids(client_id: int, product_ids: tuple) -> set:
    """
    Retrieves the set of product IDs that already exist in the database
    for the given client_id from the provided list of product_ids.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT product_id
                FROM products
                WHERE client_id = %s AND product_id IN %s
            """
            cur.execute(query, (client_id, product_ids))
            existing_ids = {row[0] for row in cur.fetchall()}
    return existing_ids

def update_record(cur, client_id: int, record: tuple):
    """
    Updates an existing product record in the database.
    record: (product_id, title, price, store_id)
    """
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

def insert_record(cur, client_id: int, record: tuple):
    """
    Inserts a new product record into the database.
    record: (product_id, title, price, store_id)
    """
    product_id, title, price, store_id = record
    insert_sql = """
        INSERT INTO products (client_id, product_id, title, price, store_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    cur.execute(insert_sql, (client_id, product_id, title, price, store_id))
    logger.info("Inserted product_id %s for client %s", product_id, client_id)

def upsert_feed_records(records: list, client_id: int):
    """
    Processes the list of feed records: for each record, update it if it exists
    or insert it if it does not.
    """
    if not records:
        logger.info("No valid records to process.")
        return

    # Prepare a tuple of product_ids from the records.
    product_ids = tuple(record[0] for record in records)
    existing_ids = get_existing_product_ids(client_id, product_ids)

    conn = get_connection()
    updated_count = 0
    inserted_count = 0
    try:
        with conn.cursor() as cur:
            for record in records:
                product_id = record[0]
                if product_id in existing_ids:
                    update_record(cur, client_id, record)
                    updated_count += 1
                else:
                    insert_record(cur, client_id, record)
                    inserted_count += 1
        conn.commit()
        logger.info(
            "Synchronization summary for client %s: Updated %d record(s), Inserted %d new record(s).", 
            client_id, updated_count, inserted_count
        )
    except Exception as e:
        logger.exception("Database error during feed import: %s", e)
        conn.rollback()
        raise e
    finally:
        conn.close()
        logger.info("Database connection closed after feed import.")

def import_feed_csv(csv_path: str, client_id: int):
    """
    High-level function that:
      1. Reads and validates the feed CSV.
      2. Upserts (updates/inserts) records into the database.
    """
    logger.info("Starting import_feed_csv with file: '%s' for client: %s", csv_path, client_id)
    records = read_feed_csv(csv_path)
    if not records:
        logger.info("No valid records found in feed CSV.")
        return
    logger.info("Parsed %d valid record(s) from CSV.", len(records))
    upsert_feed_records(records, client_id)
