import os
import logging
import unittest
from pathlib import Path
from fastapi import FastAPI
from dotenv import load_dotenv

from app.api.endpoints.products import router as products_router
from services.table_creator import TableCreator
from services.feed_importer import FeedImporter
from services.csv_reader import FeedCsvReader
from repository.product_repository import ProductRepository

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Factory to create and configure the FastAPI application."""
    app = FastAPI(title="Product Catalog Sync")

    # Include the products router
    app.include_router(products_router, prefix="/products", tags=["Products"])

    @app.on_event("startup")
    async def startup_event():

        TableCreator().create_tables()
        logger.info("Startup: Ensured tables exist.")

        tests_dir = Path(__file__).resolve().parent.parent / "tests"
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=str(tests_dir))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if not result.wasSuccessful():
            logger.error("Startup: Some unit tests FAILED!")
        else:
            logger.info("Startup: All unit tests PASSED successfully!")

        feed_csv_path = Path(__file__).resolve().parent.parent / "feed_items.csv"
        if feed_csv_path.is_file():
            logger.info(f"Startup: Populating database from {feed_csv_path} ...")
            importer = FeedImporter(ProductRepository(), FeedCsvReader())
            importer.import_feed(str(feed_csv_path), client_id=1)
            logger.info("Startup: Database populated with feed CSV after tests.")
        else:
            logger.warning(f"Startup: No feed CSV found at {feed_csv_path}. Skipping feed import.")

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )
