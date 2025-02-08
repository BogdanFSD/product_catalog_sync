import logging

logger = logging.getLogger(__name__)

class Product:

    def __init__(self, client_id: int, product_id: int, title: str, price: float, store_id: int):
        self.client_id = client_id
        self.product_id = product_id
        self.title = title
        self.price = price
        self.store_id = store_id

    def __repr__(self):
        return f"<Product(client_id={self.client_id},
        product_id={self.product_id},
        title='{self.title}',
        price={self.price},
        store_id={self.store_id})>"
