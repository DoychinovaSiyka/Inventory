from storage.json_repository import Repository
from models.movement import Movement, MovementType
from validators.movement_validator import MovementValidator
from datetime import datetime


class MovementController:
    def __init__(self, repo: Repository, product_controller, user_controller,location_controller,stocklog_controller):
        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.stocklog_controller = stocklog_controller
        self.movements = [Movement.from_dict(m) for m in self.repo.load()]

    # Internal: ID GENERATOR
    def _generate_id(self):
        if not self.movements:
            return 1
        return max(m.movement_id for m in self.movements) + 1

    # create movement
    def add(self, product_id, user_id, location_id,movement_type,
            quantity, description, price):
        # Валидации
        MovementValidator.validate_movement_type(movement_type)
        MovementValidator.validate_description(description)
        quantity = MovementValidator.parse_quantity(quantity)
        price = MovementValidator.parse_price(price)

        # Проверка дали потребителят съществува
        user = self.user_controller.get_by_id(user_id)
        if not user:
            raise ValueError(f"Потребител с ID {user_id} не съществува.")

        # Проверка дали продуктът съществува
        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

        # Проверка за локация
        location = self.location_controller.get_by_id(location_id)
        if not location:
            raise ValueError(f"Локация с ID {location_id} не съществува.")

        # Преобразуване на movement_type (ако е подаден като число)
        if isinstance(movement_type, int):
            movement_type = MovementType(movement_type)

        # Логика за IN / OUT
        if movement_type == MovementType.IN:
            product.quantity += quantity
            action = "add"
        elif movement_type == MovementType.OUT:
            if product.quantity < quantity:
                raise ValueError("Недостатъчна наличност за продажба.")
            product.quantity -= quantity
            action =  "remove"
        elif movement_type == MovementType.MOVE:
            # MOVE не променя количеството, само местоположението
            action = "move"
        product.update_modified()
        self.product_controller._save()

        # Създаване на движение
        movement = Movement(
            movement_id = self._generate_id(),
            product_id=product_id,
            user_id=user_id,
            location_id = location_id,
            movement_type=movement_type,
            quantity=quantity,
            description=description,
            price=price,
            date=str(datetime.now())
        )

        self.movements.append(movement)
        self._save()

        # Запис в STOCK LOG
        self.stocklog_controller.add_log(
            product_id = product_id,
            location_id = location_id,
            quantity = quantity,
            action = action
        )

        return movement

    # SAVE
    def _save(self):
        self.repo.save([m.to_dict() for m in self.movements])

    # GETTERS
    def get_all(self):
        return self.movements

    def get_by_id(self,movement_id):
        for m in self.movements:
            if m.movement_id == movement_id:
                return m
        return None
    def search(self, keyword):
        return [m for m in self.movements if keyword in (m.description or "").lower()]

