from storage.json_repository import JSONRepository
from models.category import Category


class ProductRepository(JSONRepository):
    def __init__(self):
        super().__init__("data/products.json")

    def load_objects(self):
        return [Category.from_dict(item) for item in self.load()]

    def save_objects(self,categories):
        self.save([c.to_dict() for c in categories])


