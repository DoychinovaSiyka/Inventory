from typing import Optional, List
import uuid
from datetime import datetime
from models.movement import Movement, MovementType
from models.invoice import Invoice
import validators.movement_validator


class MovementController:
    def __init__(self, repo, product_controller, user_controller,
                 location_controller, stocklog_controller, invoice_controller):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.stocklog_controller = stocklog_controller
        self.invoice_controller = invoice_controller

        self.movements: List[Movement] = [
            Movement.from_dict(m) for m in self.repo.load()
        ]

    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    def add(
        self,
        product_id: str,
        user_id: int,
        location_id: int,
        movement_type,
        quantity,
        description: str,
        price,
        customer: Optional[str] = None
    ) -> Movement:

        # Валидации
        validators.movement_validator.MovementValidator.validate_movement_type(movement_type)
        validators.movement_validator.MovementValidator.validate_description(description)

        quantity = validators.movement_validator.MovementValidator.parse_quantity(quantity)
        price = validators.movement_validator.MovementValidator.parse_price(price)

        # Потребител
        user = next((u for u in self.user_controller.users if u.user_id == user_id), None)
        if not user:
            raise ValueError(f"Потребител с ID {user_id} не съществува.")

        # Продукт
        product = next((p for p in self.product_controller.products if p.product_id == product_id), None)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

        # Локация
        location = next((l for l in self.location_controller.locations if l.location_id == location_id), None)
        if not location:
            raise ValueError(f"Локация с ID {location_id} не съществува.")

        # Преобразуване на movement_type, ако е подаден като число
        if isinstance(movement_type, int):
            mapping = {0: MovementType.IN, 1: MovementType.OUT, 2: MovementType.MOVE}
            if movement_type not in mapping:
                raise ValueError("Невалиден тип движение.")
            movement_type = mapping[movement_type]

        # Бизнес логика
        if movement_type == MovementType.IN:
            product.quantity += quantity
            action = "add"

        elif movement_type == MovementType.OUT:
            if product.quantity < quantity:
                raise ValueError("Недостатъчна наличност за продажба.")
            product.quantity -= quantity
            action = "remove"

        elif movement_type == MovementType.MOVE:
            action = "move"
            product.location_id = location_id

        # Обновяване на продукта
        product.update_modified()
        self.product_controller._save()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Създаване на Movement
        movement = Movement(
            movement_id=self._generate_id(),
            product_id=product_id,
            user_id=user_id,
            location_id=location_id,
            movement_type=movement_type,
            quantity=quantity,
            unit=product.unit,
            description=description,
            price=price,
            date=now,
            created=now,
            modified=now
        )

        self.movements.append(movement)
        self._save()

        # Запис в StockLog (НОВО: unit)
        self.stocklog_controller.add_log(
            product_id=product_id,
            location_id=location_id,
            quantity=quantity,
            unit=product.unit,
            action=action
        )

        # Автоматична фактура при OUT
        if movement_type == MovementType.OUT:
            customer = customer or user.username

            invoice = Invoice(
                movement_id=movement.movement_id,
                product=product.name,
                quantity=quantity,
                unit=product.unit,
                unit_price=price,
                customer=customer
            )
            self.invoice_controller.add(invoice)

        return movement

    def _save(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    def get_all(self) -> List[Movement]:
        return self.movements

    def search(self, keyword: str) -> List[Movement]:
        keyword = keyword.lower()
        return [
            m for m in self.movements
            if keyword in (m.description or "").lower()
        ]
