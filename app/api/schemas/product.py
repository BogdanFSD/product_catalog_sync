from pydantic import BaseModel

class ProductOut(BaseModel):
    product_id: int
    title: str
    price: float
    store_id: int
