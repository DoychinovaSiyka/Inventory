from storage.json_repository import JSONRepository
from models.movement import Movement


class ProductRepository(JSONRepository):
    def __init__(self):
        super().__init__("data/products.json")

    def load_objects(self):
        return [Movement.from_dict(item) for item in self.load()]

    def save_objects(self,movements):
        self.save([c.to_dict() for c in movements])


