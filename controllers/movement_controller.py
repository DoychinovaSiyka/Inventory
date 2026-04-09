from typing import Optional, List
from datetime import datetime
import uuid
from models.movement import Movement, MovementType
from validators.stock_log_validator import StockLogValidator
from models.invoice import Invoice
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator


class MovementController:
    def __init__(self, repo: JSONRepository, product_controller, user_controller,
                 location_controller, stocklog_controller, invoice_controller,
                 activity_log_controller=None,
                 inventory_controller=None):
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

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    def _validate_user_and_product(self, user_id, product_id):
        user = self.user_controller.get_by_id(user_id)
        if not user:
            raise ValueError(f"Потребител с ID {user_id} не съществува.")

        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")
        return user, product

    def _log_activity(self, user_id, movement_type, product, quantity, location_id):
        if self.activity_log:
            msg = (f"{movement_type.name} movement: product {product.name},"
                   f" qty={quantity}, loc={location_id}")
            self.activity_log.add_log(user_id, f"{movement_type.name}_MOVEMENT", msg)

    def _create_movement(self, product_id, user_id, location_id,
                         movement_type,
                         quantity, unit, description, price,
                         supplier_id=None, customer=None):

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        movement = Movement(movement_id=self._generate_id(), product_id=product_id,user_id=user_id,
                            location_id=location_id, movement_type=movement_type, quantity=quantity, unit=unit,
                            description=description, price=price, supplier_id=supplier_id, customer=customer,
                            date=now, created=now, modified=now)

        self.movements.append(movement)
        self.save_changes()
        return movement

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

            #  обновяване на inventory.json
            if self.inventory_controller:
                self.inventory_controller.increase_stock(product_id=product_id, product_name=product.name,
                                                         warehouse_id=location_id, qty=quantity)
        # OUT
        elif movement_type == MovementType.OUT:
            if product.quantity < quantity:
                raise ValueError("Недостатъчна наличност.")
            product.quantity -= quantity
            if not customer:
                raise ValueError("При OUT движение трябва да има клиент.")
            action = "remove"

            #  обновяване на inventory.json
            if self.inventory_controller:
                self.inventory_controller.decrease_stock(product_id=product_id, warehouse_id=location_id,
                                                         qty=quantity)
        product.update_modified()
        self.product_controller.save_changes()

        movement = self._create_movement(product_id, user_id, location_id,movement_type, quantity,
                                         product.unit, description, price,
                                         supplier_id=supplier_id, customer=customer)

        self.stocklog_controller.add_log(product_id, location_id, quantity, product.unit, action)
        self._log_activity(user_id, movement_type, product, quantity, location_id)

        if movement_type == MovementType.OUT:
            invoice = Invoice(movement_id=movement.movement_id, product=product.name, quantity=quantity,
                              unit=product.unit, unit_price=price, customer=customer)
            self.invoice_controller.add(invoice)

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

        #  Проверка на наличностите в inventory.json
        record = self.inventory_controller._find(product_id, from_location_id)
        if not record or record["quantity"] < quantity:
            raise ValueError("Недостатъчна наличност в този склад.")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        move_entry = Movement(movement_id=self._generate_id(), product_id=product_id,
            user_id=user_id, location_id=to_location_id, movement_type=MovementType.MOVE,
            quantity=quantity, unit=product.unit,
            description=f"Преместване от {from_location_id} към {to_location_id}. {description}",
            price=0,supplier_id=None,customer=None,from_location_id=from_location_id,
            to_location_id=to_location_id, date=now, created=now, modified=now)

        self.movements.append(move_entry)
        self.save_changes()

        # Преместване
        self.inventory_controller.move_stock(product_id=product_id, product_name=product.name,
                                             from_wh=from_location_id, to_wh=to_location_id, qty=quantity)

        self.stocklog_controller.add_log(product_id, from_location_id, quantity, product.unit, "move_out")
        self.stocklog_controller.add_log(product_id, to_location_id, quantity, product.unit, "move_in")

        if self.activity_log:
            self.activity_log.add_log(user_id, "MOVE_PRODUCT", f"Moved {product.name} to {to_location_id}")

        return move_entry

    def search(self, keyword: str):
        keyword = keyword.lower()
        results = []

        for m in self.movements:
            desc = (m.description or "").lower()
            product = self.product_controller.get_by_id(m.product_id)
            product_name = (product.name if product else "").lower()
            movement_type = m.movement_type.name.lower()
            customer = (m.customer or "").lower()
            supplier = (m.supplier_id or "").lower()

            if (keyword in desc or keyword in product_name or keyword in movement_type or
                    keyword in customer or keyword in supplier):
                results.append(m)

        return results

    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    def get_all(self) -> List[Movement]:
        return self.movements
