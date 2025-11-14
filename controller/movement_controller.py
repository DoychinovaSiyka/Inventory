
from storage.json_repository import Repository

from models.movement import Movement, MovementType


class MovementController():
    def __init__(self, repo:Repository):
        self.repo = repo
        self.movements = [Movement.from_dict(p) for p in self.repo.load()]


    def add(self,product_id,movement_type,quantity,description,price):
        movement = Movement(product_id,movement_type,quantity,description,price )
        self.movements.append(movement)
        self._save()
        return movement

    def _save(self):
        self.repo.save([m.to_dict() for m in self.movements])
    def search(self,keyword):
        return [p for p in self.movements if keyword in (p.description or "").lower()]

    def get_all(self):
        return self.movements



