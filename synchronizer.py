import csv
from db import get_connection

def read_portal_csv(csv_path: str):
    """
    Returns a dict {product_id: { title, price, store_id }}.
    """
    data = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = int(row["product_id"])
            data[pid] = {
                "title": row["title"],
                "price": float(row["price"]),
                "store_id": int(row["store_id"])
            }
    return data

def fetch_db_products(client_id: int):
    """
    Returns a dict {product_id: { title, price, store_id }} from the DB.
    """
    results = {}
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT product_id, title, price, store_id
                FROM products
                WHERE client_id = %s
            """, (client_id,))
            for row in cur.fetchall():
                pid, title, price, store_id = row
                results[pid] = {
                    "title": title,
                    "price": float(price),
                    "store_id": store_id
                }
    finally:
        conn.close()
    return results

def synchronize_portal(csv_path: str, client_id: int):
    """
    Compare the DB data to the portal CSV and apply:
    - Deletion (DB only, not in CSV)
    - Update (DB & CSV differ)
    - Insert (CSV but not DB)
    """
    portal_data = read_portal_csv(csv_path)
    db_data = fetch_db_products(client_id)

    # Determine what to delete/update/insert
    to_delete = []
    to_update = []
    to_insert = []

    # Check DB items
    for pid, db_vals in db_data.items():
        if pid not in portal_data:
            to_delete.append(pid)
        else:
            # check differences
            p_vals = portal_data[pid]
            if (db_vals["title"] != p_vals["title"] or
                db_vals["price"] != p_vals["price"] or
                db_vals["store_id"] != p_vals["store_id"]):
                to_update.append((pid, p_vals))

    # Check for new items in portal CSV
    for pid, p_vals in portal_data.items():
        if pid not in db_data:
            to_insert.append((pid, p_vals))

    # Apply changes
    apply_changes(client_id, to_delete, to_update, to_insert)

def apply_changes(client_id, to_delete, to_update, to_insert):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Deletions
            if to_delete:
                cur.execute("""
                    DELETE FROM products
                    WHERE client_id = %s AND product_id = ANY(%s)
                """, (client_id, to_delete))
                print(f"Deleted {cur.rowcount} products for client {client_id}.")

            # Updates
            update_sql = """
                UPDATE products
                SET title = %s,
                    price = %s,
                    store_id = %s,
                    updated_at = NOW()
                WHERE client_id = %s AND product_id = %s
            """
            for (pid, p_vals) in to_update:
                cur.execute(update_sql, (
                    p_vals["title"],
                    p_vals["price"],
                    p_vals["store_id"],
                    client_id,
                    pid
                ))
                print(f"Updated product_id={pid} for client {client_id}.")

            # Inserts
            insert_sql = """
                INSERT INTO products (client_id, product_id, title, price, store_id)
                VALUES (%s, %s, %s, %s, %s)
            """
            for (pid, p_vals) in to_insert:
                cur.execute(insert_sql, (
                    client_id,
                    pid,
                    p_vals["title"],
                    p_vals["price"],
                    p_vals["store_id"]
                ))
            if to_insert:
                print(f"Inserted {len(to_insert)} new products for client {client_id}.")

        conn.commit()
    finally:
        conn.close()
