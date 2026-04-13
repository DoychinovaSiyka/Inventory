from typing import Optional, List
from datetime import datetime
import uuid
from models.movement import Movement, MovementType
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator


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

        for m in raw:
            if not m.get("movement_id"):
                m["movement_id"] = self._generate_id()
            self.movements.append(Movement.from_dict(m))

        self.save_changes()

    # Генериране на UUID
    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    # Проверка за валидни потребител и продукт
    def _validate_user_and_product(self, user_id, product_id):
        user = self.user_controller.get_by_id(user_id)
        if not user:
            raise ValueError(f"Потребител с ID {user_id} не съществува.")

        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

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

        MovementValidator.validate_movement_type(movement_type)
        MovementValidator.validate_description(description)

        quantity = round(float(MovementValidator.parse_quantity(quantity)), 2)
        price = round(float(MovementValidator.parse_price(price)), 2)

        user, product = self._validate_user_and_product(user_id, product_id)

        if isinstance(movement_type, int):
            mapping = {0: MovementType.IN, 1: MovementType.OUT, 2: MovementType.MOVE}
            movement_type = mapping.get(movement_type)
            if not movement_type:
                raise ValueError("Невалиден тип движение.")

        if movement_type == MovementType.MOVE:
            raise ValueError("MOVE може да се извършва само чрез move_product().")

        # IN
        if movement_type == MovementType.IN:
            product.quantity += quantity
            product.location_id = location_id

            if supplier_id is None:
                raise ValueError("При IN движение трябва да има доставчик.")

            action = "add"

            if self.inventory_controller:
                self.inventory_controller.increase_stock(
                    product_id=product_id,
                    product_name=product.name,
                    warehouse_id=location_id,
                    qty=quantity
                )

        # OUT
        elif movement_type == MovementType.OUT:
            if product.quantity < quantity:
                raise ValueError("Недостатъчна наличност.")

            product.quantity -= quantity

            if not customer:
                raise ValueError("При OUT движение трябва да има клиент.")

            action = "remove"

            if self.inventory_controller:
                self.inventory_controller.decrease_stock(
                    product_id=product_id,
                    warehouse_id=location_id,
                    qty=quantity
                )

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

        if from_location_id == to_location_id:
            raise ValueError("MOVE трябва да е между различни локации.")

        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт {product_id} не съществува.")

        quantity = round(float(quantity), 2)

        record = self.inventory_controller._find(product_id, from_location_id)
        if not record or record["quantity"] < quantity:
            raise ValueError("Недостатъчна наличност в този склад.")

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
        keyword = keyword.lower().strip()
        return [m for m in self.movements if keyword in (m.description or "").lower()]

    # Разширено филтриране
    def advanced_filter(self, movement_type=None, start_date=None, end_date=None,
                        product_id=None, location_id=None, user_id=None):

        results = self.movements

        if movement_type:
            results = [m for m in results if m.movement_type == movement_type]

        if start_date or end_date:
            results = self.filter_by_date_range(start_date, end_date)

        if product_id:
            results = [m for m in results if m.product_id == product_id]

        if location_id is not None:
            results = [m for m in results if m.location_id == location_id]

        if user_id is not None:
            results = [m for m in results if m.user_id == user_id]

        return results

    # Избор на продукт
    def select_product(self):
        products = self.product_controller.get_all()
        if not products:
            print("Няма продукти.")
            return None

        print("\nИзберете продукт:")
        for i, p in enumerate(products):
            print(f"{i}. {p.name} ({p.quantity} {p.unit})")

        raw = input("Избор: ")
        try:
            index = MovementValidator.validate_index(raw, len(products), "продукт")
            return products[index]
        except ValueError as e:
            print(e)
            return None

    # Избор на локация
    def select_location(self, label="локация"):
        locations = self.location_controller.get_all()
        if not locations:
            print("Няма налични локации.")
            return None

        print(f"\nИзберете {label}:")
        for i, loc in enumerate(locations):
            print(f"{i}. {loc.name} (ID: {loc.location_id})")

        raw = input("Избор: ")
        try:
            index = MovementValidator.validate_index(raw, len(locations), label)
            return locations[index]
        except ValueError as e:
            print(e)
            return None

    # Избор на доставчик
    def select_supplier(self):
        suppliers = self.product_controller.supplier_controller.get_all()
        if not suppliers:
            print("Няма доставчици.")
            return None

        print("\nИзберете доставчик:")
        for i, s in enumerate(suppliers):
            print(f"{i}. {s.name}")

        raw = input("Доставчик: ")
        try:
            index = MovementValidator.validate_index(raw, len(suppliers), "доставчик")
            return suppliers[index].supplier_id
        except ValueError as e:
            print(e)
            return None

    # Данни за печат
    def get_display_data(self, movement):
        product = self.product_controller.get_by_id(movement.product_id)
        user = self.user_controller.get_by_id(movement.user_id)
        location = self.location_controller.get_by_id(movement.location_id)

        supplier = None
        if movement.supplier_id:
            supplier = self.product_controller.supplier_controller.get_by_id(movement.supplier_id)

        return {
            "product": product.name if product else f"ID: {movement.product_id}",
            "user": user.username if user else f"ID: {movement.user_id}",
            "location": location.name if location else "—",
            "movement_type": movement.movement_type,
            "quantity": movement.quantity,
            "unit": movement.unit,
            "price": movement.price,
            "description": movement.description,
            "supplier": supplier.name if supplier else "—",
            "customer": movement.customer,
            "date": movement.date,
            "id": movement.movement_id
        }

    # Форматиране за печат
    def format_movement(self, movement):
        data = self.get_display_data(movement)

        return (
            f"Продукт: {data['product']}\n"
            f"Потребител: {data['user']}\n"
            f"Локация: {data['location']}\n"
            f"Тип: {data['movement_type']}\n"
            f"Количество: {data['quantity']} {data['unit']}\n"
            f"Цена: {data['price']}\n"
            f"Описание: {data['description']}\n"
            f"Доставчик: {data['supplier']}\n"
            f"Клиент: {data['customer']}\n"
            f"Дата: {data['date']}\n"
            f"ID: {data['id']}\n"
            "----------------------------------------"
        )

    # Записване
    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    # Всички движения
    def get_all(self) -> List[Movement]:
        return self.movements
