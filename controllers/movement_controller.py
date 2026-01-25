from storage.json_repository import Repository
from models.movement import Movement
from validators.movement_validator import MovementValidator


class MovementController:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.movements = [Movement.from_dict(p) for p in self.repo.load()]

    def add(self, product_id, movement_type, quantity, description, price):
        MovementValidator.validate_movement_type(movement_type)
        quantity = MovementValidator.parse_quantity(quantity)
        price = MovementValidator.parse_price(price)
        MovementValidator.validate_description(description)

        movement = Movement(product_id, movement_type, quantity, description, price)
        self.movements.append(movement)
        self._save()
        return movement

    def _save(self):
        self.repo.save([m.to_dict() for m in self.movements])

    def get_all(self):
        return self.movements

    def search(self, keyword):
        return [m for m in self.movements if keyword in (m.description or "").lower()]
