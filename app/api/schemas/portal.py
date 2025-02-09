from pydantic import BaseModel

class PortalSyncResponse(BaseModel):
    message: str
    deleted: int
    inserted: int
    updated: int
