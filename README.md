# product_catalog_sync

# Product Catalog Sync (Version 4)

A tool to import product data from CSV files into a PostgreSQL database and synchronize the database with portal data.

- **CLI usage** for importing and synchronizing.
- A **FastAPI** application with endpoints to perform feed import, portal sync, and combined feed+sync.
- **Docker** configuration (Dockerfile + docker-compose) to run both the application and a PostgreSQL container.



---

## Features

1. **CSV Feed Import**  
   Reads a CSV file (columns: `product_id`, `title`, `price`, `store_id`) and upserts records into a `products` table based on `(client_id, product_id)`.

2. **Portal Synchronization**  
   Reads a second CSV to identify products to **insert**, **update**, or **delete** in the database.

3. **CLI Tool** (`cli.py`)  
   - **`--feed`**: The feed CSV path (required).  
   - **`--portal`**: The optional portal CSV path.  
   - **`--client`**: The client ID (defaults to 1).

4. **FastAPI Endpoints**  
   - **List Products**: `GET /products?client_id={some_id}`  
   - **Import Feed**: `POST /products/feed?client_id={some_id}`  
   - **Portal Sync**: `POST /products/portal-sync?client_id={some_id}`  
   - **Feed + Sync**: `POST /products/feed-and-sync?client_id={some_id}`  
   - **Health Check**: `GET /health` (returns `{"status": "ok"}`).

5. **Automated Tests**  
   - **Unit tests** in `tests/unit/`.  
   - **Integration tests** in `tests/integration/`, which use a real or mocked database.  
   - Tests run automatically on startup (in `app.main`) and log results.

---

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

By default, the app automatically creates the products table on startup. If you want to verify manually:

```
psql -U postgres -d your_db_name -h localhost -W
# Inside psql:
\dt                 # List tables
SELECT * FROM products LIMIT 10;  # View data
```

## Usage

### Running the CLI


Provided a CLI script (cli.py) which:

- Creates tables if needed.
- Imports a feed CSV (--feed).
- Optionally synchronizes with a portal CSV (--portal).
Examples:

1. Import Only:
```
python cli.py --feed path/to/feed_items.csv --client 1
```

- Required: --feed
- Optional: --client

2. Import + Portal Sync:

```
python cli.py --feed feed_items.csv --portal portal_items.csv --client 1
```
- The script imports the feed first, then does a portal sync if --portal is given.

### Using the FastAPI Server

Start the FastAPI application:

```
uvicorn app.main:app --reload
```

Access the API documentation at:

- http://localhost:8000/docs

- http://localhost:8000/redoc

## API Endpoints

- List Products: GET /products?client_id=1

- Import Feed: POST /products/feed

- Sync with Portal: POST /products/portal-sync

- Feed & Sync Combined: POST /products/feed-and-sync
- Health check : GET /health

## Example API Request (Using curl)

```
curl -X POST "http://localhost:8000/products/feed" \
  -F "file=@feed_items.csv" \
  -F "client_id=1"
```

## Docker Usage

### 1. Docker Compose (Recommended)
This repo includes a docker-compose.yml that:

- Runs PostgreSQL as bohdanfsd-db (hidden from host, accessible internally at db:5432).
- Runs FastAPI in a separate container as bohdanfsd-app, exposed on port 8000.

Steps:

1. Create a secret for your DB password:

```
mkdir -p secrets
echo "MySecurePassword" > secrets/db_password.txt
```

2. Build and run:

```
docker-compose build
docker-compose up -d
```

3. Check logs (optional):

```
docker-compose logs -f
```

4. Access the API:

- http://localhost:8000/docs for Swagger UI.
- http://localhost:8000/health to confirm healthy status.

### 2. Pull from Docker Hub
If you just want to run the app image from Docker Hub:

```
docker pull bohdanfsd/product_catalog_sync:latest
```

Then run (assuming you have your own DB or link to one):

```
docker run -d \
  -p 8000:8000 \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=5432 \
  -e DB_USER=postgres \
  -e DB_PASSWORD=MySecurePassword \
  --name bohdanfsd-app \
  bohdanfsd/product_catalog_sync:latest
  ```
Adjust environment variables to match your setup.

## Check Data in PostgreSQL
```
psql -U postgres -d your_db_name -h localhost -W
# Inside psql:
\dt                 # List tables
SELECT * FROM products LIMIT 10;  # View products
```


Tests
All tests (unit + integration) automatically run on FastAPI startup (in startup_event of app.main). If any test fails, you’ll see a log message: “Some unit tests FAILED!”.

You can also run tests manually:

- All tests:

```
python -m unittest discover -s tests
```

- Only integration tests:

```
python -m unittest discover -s tests/integration
```

- Only unit tests:

```
python -m unittest discover -s tests/unit
```
