import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List

from repository.product_repository import ProductRepository
from services.feed_importer import FeedImporter
from services.portal_synchronizer import PortalSynchronizer
from services.csv_reader import FeedCsvReader
from db.connection import DatabaseConnection


from app.api.schemas.product import ProductOut
from app.api.schemas.feed import FeedImportResponse
from app.api.schemas.portal import PortalSyncResponse


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[ProductOut])
def list_products(client_id: int = Query(..., description="Client ID")) -> List[ProductOut]:
    """
    Return a list of products for the given client_id as a list of ProductOut.
    """
    try:
        db_conn = DatabaseConnection().get_connection()
        with db_conn.cursor() as cur:
            cur.execute(
                "SELECT product_id, title, price, store_id FROM products WHERE client_id = %s",
                (client_id,)
            )
            rows = cur.fetchall()
            # Convert DB rows to list of ProductOut
            results = [
                ProductOut(
                    product_id=row[0],
                    title=row[1],
                    price=float(row[2]),
                    store_id=row[3]
                )
                for row in rows
            ]
            return results
    except Exception as e:
        logger.exception("Error listing products: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if 'db_conn' in locals():
            db_conn.close()

@router.post("/feed", response_model=FeedImportResponse)
async def import_feed(
    client_id: int = Query(..., description="Client ID"),
    file: UploadFile = File(...),
) -> FeedImportResponse:
    """
    Import a feed CSV for the given client_id. This upserts products in the DB.
    Returns a FeedImportResponse.
    """
    try:
        csv_content = await file.read()
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as f:
            f.write(csv_content)

        importer = FeedImporter(ProductRepository(), FeedCsvReader())
        importer.import_feed(temp_file_path, client_id)

        return FeedImportResponse(message="Feed imported successfully.")
    except Exception as e:
        logger.exception("Error importing feed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portal-sync", response_model=PortalSyncResponse)
async def sync_portal(
    client_id: int = Query(..., description="Client ID"),
    file: UploadFile = File(...),
) -> PortalSyncResponse:
    """
    Synchronize the DB with a 'portal' CSV:
      - Delete products not in CSV
      - Update changed products
      - Insert new products

    Returns a PortalSyncResponse summarizing the actions.
    """
    try:
        csv_content = await file.read()
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as f:
            f.write(csv_content)

        synchronizer = PortalSynchronizer()
        portal_records = synchronizer.read_portal_csv(temp_file_path)
        if not portal_records:
            return PortalSyncResponse(message="No valid portal records found.", deleted=0, inserted=0, updated=0)

        db_products = synchronizer.fetch_db_products(client_id)
        to_delete, to_insert, to_update = synchronizer.compute_sync_actions(db_products, portal_records)
        synchronizer.apply_sync_actions(client_id, to_delete, to_insert, to_update)

        return PortalSyncResponse(
            message="Portal synchronization completed.",
            deleted=len(to_delete),
            inserted=len(to_insert),
            updated=len(to_update)
        )
    except Exception as e:
        logger.exception("Error during portal sync: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feed-and-sync", response_model=PortalSyncResponse)
async def feed_and_sync(
    client_id: int = Query(..., description="Client ID"),
    feed_file: UploadFile = File(...),
    portal_file: UploadFile = File(...),
) -> PortalSyncResponse:
    """
    Single endpoint that:
      1) Imports a feed CSV (upserting products)
      2) Synchronizes the DB with a 'portal' CSV
    Returns a PortalSyncResponse summarizing the final sync actions.
    """
    try:
        feed_csv_content = await feed_file.read()
        feed_temp_file = f"/tmp/{feed_file.filename}"
        with open(feed_temp_file, "wb") as f:
            f.write(feed_csv_content)

        importer = FeedImporter(ProductRepository(), FeedCsvReader())
        importer.import_feed(feed_temp_file, client_id)

        portal_csv_content = await portal_file.read()
        portal_temp_file = f"/tmp/{portal_file.filename}"
        with open(portal_temp_file, "wb") as f:
            f.write(portal_csv_content)

        synchronizer = PortalSynchronizer()
        portal_records = synchronizer.read_portal_csv(portal_temp_file)
        if not portal_records:
            return PortalSyncResponse(message="No valid portal records found.", deleted=0, inserted=0, updated=0)

        db_products = synchronizer.fetch_db_products(client_id)
        to_delete, to_insert, to_update = synchronizer.compute_sync_actions(db_products, portal_records)
        synchronizer.apply_sync_actions(client_id, to_delete, to_insert, to_update)

        return PortalSyncResponse(
            message="Feed import + Portal synchronization completed.",
            deleted=len(to_delete),
            inserted=len(to_insert),
            updated=len(to_update)
        )
    except Exception as e:
        logger.exception("Error during feed-and-sync: %s", e)
        raise HTTPException(status_code=500, detail=str(e))