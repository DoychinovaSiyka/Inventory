from storage.json_repository import Repository
from models.movement import Movement, MovementType
from validators.movement_validator import MovementValidator


class MovementController:
    def __init__(self, repo: Repository, product_controller, user_controller):
        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.movements = [Movement.from_dict(m) for m in self.repo.load()]

    def add(self, product_id, movement_type, quantity, description, price):
        # Валидации
        MovementValidator.validate_movement_type(movement_type)
        quantity = MovementValidator.parse_quantity(quantity)
        price = MovementValidator.parse_price(price)
        MovementValidator.validate_description(description)

        # Преобразуване на movement_type (0/1 -> Enum)
        if isinstance(movement_type, int):
            movement_type = MovementType.IN if movement_type == 0 else MovementType.OUT

        # Проверка дали продуктът съществува
        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

        # Логика за IN / OUT
        if movement_type == MovementType.IN:
            product.quantity += quantity
        elif movement_type == MovementType.OUT:
            if product.quantity < quantity:
                raise ValueError("Недостатъчна наличност за продажба.")
            product.quantity -= quantity

        product.update_modified()
        self.product_controller._save()

        # Създаване на движение
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
