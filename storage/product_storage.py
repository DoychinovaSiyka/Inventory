from storage.json_repository import JSONRepository
from models.product import Product

class ProductRepository(JSONRepository):
    def __init__(self):
        super().__init__("data/products.json")

    def load_objects(self):
        return [Product.from_dict(item) for item in self.load()]

    def save_objects(self,products):
        self.save([p.to_dict() for p in products])


