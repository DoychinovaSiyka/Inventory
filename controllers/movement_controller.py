from typing import Optional, List
from datetime import datetime
import uuid
from models.movement import Movement, MovementType
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator

from filters.movement_filters import (filter_by_description, filter_advanced)


class MovementController:
    def __init__(self, repo: JSONRepository, product_controller, user_controller,
                 location_controller, stocklog_controller, invoice_controller,
                 activity_log_controller=None, inventory_controller=None):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.stocklog_controller = stocklog_controller
        self.invoice_controller = invoice_controller
        self.activity_log = activity_log_controller
        self.inventory_controller = inventory_controller

        raw = self.repo.load()
        self.movements: List[Movement] = []

        # Зареждам движенията от JSON
        for m in raw:
            if not m.get("movement_id"):
                m["movement_id"] = self._generate_id()
            self.movements.append(Movement.from_dict(m))

        self.save_changes()

    # Генериране на UUID
    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    # Проверка за валидни потребител и продукт (валидаторът проверява, контролерът само извиква)
    def _validate_user_and_product(self, user_id, product_id):
        MovementValidator.validate_user_exists(user_id, self.user_controller)
        MovementValidator.validate_product_exists(product_id, self.product_controller)

        user = self.user_controller.get_by_id(user_id)
        product = self.product_controller.get_by_id(product_id)
        return user, product

    # Логване на активност
    def _log_activity(self, user_id, movement_type, product, quantity, location_id):
        if self.activity_log:
            msg = f"{movement_type.name} movement: product {product.name}, qty={quantity}, loc={location_id}"
            self.activity_log.add_log(user_id, f"{movement_type.name}_MOVEMENT", msg)

    # Създаване на движение
    def _create_movement(self, product_id, user_id, location_id, movement_type,
                         quantity, unit, description, price,
                         supplier_id=None, customer=None):

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        movement = Movement(
            movement_id=self._generate_id(),
            product_id=product_id,
            user_id=user_id,
            location_id=location_id,
            movement_type=movement_type,
            quantity=quantity,
            unit=unit,
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
        return movement

    # Връщане по ID
    def get_by_id(self, movement_id):
        movement_id = str(movement_id)
        return next((m for m in self.movements if str(m.movement_id) == movement_id), None)

    # IN / OUT
    def add(self, product_id: str, user_id: str, location_id: str, movement_type,
            quantity, description: str, price, customer: Optional[str] = None,
            supplier_id: Optional[str] = None) -> Movement:

        # Валидации (всичко е изнесено)
        MovementValidator.validate_movement_type(movement_type)
        MovementValidator.validate_description(description)
        quantity = MovementValidator.parse_quantity(quantity)
        price = MovementValidator.parse_price(price)

        user, product = self._validate_user_and_product(user_id, product_id)
        movement_type = MovementValidator.normalize_movement_type(movement_type)

        # Бизнес правила за IN/OUT (валидаторът ги проверява)
        MovementValidator.validate_in_out_rules(
            movement_type, product, quantity, supplier_id, customer
        )

        # IN
        if movement_type == MovementType.IN:
            product.quantity += quantity
            product.location_id = location_id

            if self.inventory_controller:
                self.inventory_controller.increase_stock(
                    product_id=product_id,
                    product_name=product.name,
                    warehouse_id=location_id,
                    qty=quantity
                )
            action = "add"

        # OUT
        elif movement_type == MovementType.OUT:
            product.quantity -= quantity

            if self.inventory_controller:
                self.inventory_controller.decrease_stock(
                    product_id=product_id,
                    warehouse_id=location_id,
                    qty=quantity
                )
            action = "remove"

        product.update_modified()
        self.product_controller.save_changes()

        movement = self._create_movement(
            product_id, user_id, location_id, movement_type,
            quantity, product.unit, description, price,
            supplier_id=supplier_id, customer=customer
        )

        self.stocklog_controller.add_log(product_id, location_id, quantity, product.unit, action)
        self._log_activity(user_id, movement_type, product, quantity, location_id)

        if movement_type == MovementType.OUT:
            self.invoice_controller.create_invoice_for_out(movement, product)

        return movement

    # MOVE
    def move_product(self, product_id: str, user_id: str, from_location_id: str,
                     to_location_id: str, quantity: float, description: str = ""):

        # Валидации (всичко е изнесено)
        MovementValidator.validate_move_locations(from_location_id, to_location_id)
        MovementValidator.validate_product_exists(product_id, self.product_controller)
        quantity = MovementValidator.parse_quantity(quantity)
        MovementValidator.validate_move_stock(
            product_id, from_location_id, quantity, self.inventory_controller
        )

        product = self.product_controller.get_by_id(product_id)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        move_entry = Movement(
            movement_id=self._generate_id(),
            product_id=product_id,
            user_id=user_id,
            location_id=to_location_id,
            movement_type=MovementType.MOVE,
            quantity=quantity,
            unit=product.unit,
            description=f"Преместване от {from_location_id} към {to_location_id}. {description}",
            price=0,
            supplier_id=None,
            customer=None,
            from_location_id=from_location_id,
            to_location_id=to_location_id,
            date=now,
            created=now,
            modified=now
        )

        self.movements.append(move_entry)
        self.save_changes()

        self.inventory_controller.move_stock(
            product_id=product_id,
            product_name=product.name,
            from_wh=from_location_id,
            to_wh=to_location_id,
            qty=quantity
        )

        self.stocklog_controller.add_log(product_id, from_location_id, quantity, product.unit, "move_out")
        self.stocklog_controller.add_log(product_id, to_location_id, quantity, product.unit, "move_in")

        if self.activity_log:
            self.activity_log.add_log(user_id, "MOVE_PRODUCT", f"Moved {product.name} to {to_location_id}")

        return move_entry

    # Търсене по описание
    def search_by_description(self, keyword):
        return filter_by_description(self.movements, keyword)

    # Разширено филтриране
    def advanced_filter(self, movement_type=None, start_date=None, end_date=None,
                        product_id=None, location_id=None, user_id=None):

        return filter_advanced(
            self.movements,
            movement_type=movement_type,
            start_date=start_date,
            end_date=end_date,
            product_id=product_id,
            location_id=location_id,
            user_id=user_id
        )

    # Записване
    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    # Всички движения
    def get_all(self) -> List[Movement]:
        return self.movements
