from typing import Optional, List
from datetime import datetime
from models.movement import Movement, MovementType
from models.invoice import Invoice
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator


class MovementController:
    def __init__(self, repo: JSONRepository, product_controller, user_controller,
                 location_controller, stocklog_controller, invoice_controller,
                 activity_log_controller=None):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.stocklog_controller = stocklog_controller
        self.invoice_controller = invoice_controller
        self.activity_log = activity_log_controller

        self.movements: List[Movement] = [Movement.from_dict(m) for m in self.repo.load()]

    def _generate_id(self) -> int:
        if not self.movements:
            return 1
        return max(m.movement_id for m in self.movements) + 1

    def add(self, product_id: str, user_id: str, location_id: str, movement_type,
            quantity, description: str, price, customer: Optional[str] = None,
            supplier_id: Optional[str] = None) -> Movement:

        # Валидации
        MovementValidator.validate_movement_type(movement_type)
        MovementValidator.validate_description(description)

        # Парсване + нормализиране на числата
        quantity = MovementValidator.parse_quantity(quantity)
        price = MovementValidator.parse_price(price)

        quantity = round(float(quantity), 2)
        price = round(float(price), 2)

        # Проверка за потребител
        user = self.user_controller.get_by_id(user_id)
        if not user:
            raise ValueError(f"Потребител с ID {user_id} не съществува.")

        # Проверка за продукт
        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

        # Преобразуване на movement_type
        if isinstance(movement_type, int):
            mapping = {0: MovementType.IN, 1: MovementType.OUT, 2: MovementType.MOVE}
            movement_type = mapping.get(movement_type)
            if not movement_type:
                raise ValueError("Невалиден тип движение.")

        if movement_type == MovementType.MOVE:
            raise ValueError("MOVE може да се извършва само чрез move_product().")

        # Логика за IN / OUT
        if movement_type == MovementType.IN:
            product.quantity += quantity
            product.location_id = location_id
            if supplier_id is None:
                raise ValueError("При IN движение трябва да има доставчик.")
            action = "add"

        elif movement_type == MovementType.OUT:
            if product.quantity < quantity:
                raise ValueError("Недостатъчна наличност.")
            product.quantity -= quantity
            if not customer:
                raise ValueError("При OUT движение трябва да има клиент.")
            action = "remove"

        # Обновяване на продукта
        product.update_modified()
        self.product_controller.save_changes()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
            supplier_id=supplier_id,
            customer=customer,
            date=now,
            created=now,
            modified=now
        )

        self.movements.append(movement)
        self.save_changes()

        # Логване в stocklog
        self.stocklog_controller.add_log(product_id, location_id, quantity, product.unit, action)

        # Логване в activity log
        if self.activity_log:
            log_msg = f"{movement_type.name} movement: product {product.name}, qty={quantity}, loc={location_id}"
            self.activity_log.add_log(user_id, f"{movement_type.name}_MOVEMENT", log_msg)

        # Генериране на фактура при OUT
        if movement_type == MovementType.OUT:
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

    def move_product(self, product_id: str, user_id: str, from_location_id: str,
                     to_location_id: str, quantity: float, description: str = ""):

        if from_location_id == to_location_id:
            raise ValueError("MOVE трябва да е между различни локации.")

        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт {product_id} не съществува.")

        # Нормализиране на quantity и проверка
        quantity = round(float(quantity), 2)

        if product.quantity < quantity:
            raise ValueError("Недостатъчна наличност за преместване.")

        product.location_id = to_location_id
        product.update_modified()
        self.product_controller.save_changes()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        m_id = self._generate_id()
        move_entry = Movement(
            movement_id=m_id,
            product_id=product_id,
            user_id=user_id,
            location_id=to_location_id,
            movement_type=MovementType.MOVE,
            quantity=quantity,
            unit=product.unit,
            description=f"Преместване от {from_location_id} към {to_location_id}. {description}",
            price=0,
            customer=None,
            supplier_id=None,
            date=now,
            created=now,
            modified=now
        )

        self.movements.append(move_entry)
        self.save_changes()

        self.stocklog_controller.add_log(product_id, from_location_id, quantity, product.unit, "move_out")
        self.stocklog_controller.add_log(product_id, to_location_id, quantity, product.unit, "move_in")

        if self.activity_log:
            self.activity_log.add_log(user_id, "MOVE_PRODUCT",
                                      f"Moved {product.name} to {to_location_id}")

        return move_entry

    # Филтри и помощни методи
    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    def get_all(self) -> List[Movement]:
        return self.movements
