# product_catalog_sync

# Product Catalog Sync (Version 2)

A tool to import product data from CSV files into a PostgreSQL database and synchronize the database with portal data.


## Requirements
- Python 3.9+
- PostgreSQL server running locally (or accessible via network)

## Installation

1. Clone repo

```
git clone https://github.com/BogdanFSD/product_catalog_sync.git
```


2. Switch to project directory

```
cd product_catalog_sync
```

3. Create a virtual environment:

```
   python -m venv venv
# Activate the virtual environment:
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

4. Install dependencies

```
pip install -r requirements.txt
```

5. Set Up Environment Variables

- Copy the sample environment file:
```
cp .sample.env .env
```

- Open .env and update the placeholders with your PostgreSQL credentials:
```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```


## Database Setup

The script will automatically:

- Create the products table if it doesn’t exist.
- Insert or update records based on client_id and product_id.

To manually check the database:

```
psql -U postgres -d your_db_name -h localhost -W
# Inside psql:
\dt                 # List tables
SELECT * FROM products LIMIT 10;  # View data
```

## Usage

1. Run the importer with the following command:
```
python main.py --feed path/to/feed_items.csv --client 1
```

- --feed (required): Path to the CSV file (e.g., feed_items.csv)

- --client (optional): Client ID (defaults to 1 if not provided)

2. Import + Synchronize with Portal CSV
```
python main.py --feed feed_items.csv --portal portal_items.csv --client 1
```

- --portal (optional): Path to the portal CSV file for synchronization.

The process:
- Import products from feed_items.csv.
- Compare the database with portal_items.csv:
- Insert new products from the portal.
- Update products with changed details.
- Delete products missing from the portal.

## Check Data in PostgreSQL
```
psql -U postgres -d your_db_name -h localhost -W
# Inside psql:
\dt                 # List tables
SELECT * FROM products LIMIT 10;  # View products
```
