from pydantic import BaseModel

class FeedImportResponse(BaseModel):
    message: str
