import csv
from db import get_connection

def import_feed_csv(csv_path: str, client_id: int):
    """
    Reads feed_items.csv and inserts or updates records in the products table.
    """
    records = []

    # Read CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Basic validation
            product_id = int(row["product_id"])
            title = row["title"]
            price = float(row["price"])
            store_id = int(row["store_id"])
            records.append((product_id, title, price, store_id))
    
    # Upsert in DB
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            upsert_sql = """
                INSERT INTO products (client_id, product_id, title, price, store_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (client_id, product_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    price = EXCLUDED.price,
                    store_id = EXCLUDED.store_id,
                    updated_at = NOW();
            """
            for (product_id, title, price, store_id) in records:
                cur.execute(upsert_sql, (client_id, product_id, title, price, store_id))
        conn.commit()
    finally:
        conn.close()

    print(f"Imported {len(records)} records for client {client_id}.")
