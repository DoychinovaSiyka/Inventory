from typing import Optional, List
from datetime import datetime
import uuid
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
        # Зареждаме движенията от JSON
        raw = self.repo.load()
        self.movements: List[Movement] = []

        # гарантираме, че всяко движение има UUID
        for m in raw:
            if not m.get("movement_id"):
                m["movement_id"] = self._generate_id()
            self.movements.append(Movement.from_dict(m))
        # Записваме поправените ID обратно
        self.save_changes()

    #  Генериране на UUID за движение
    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    # Проверка за валиден потребител и продукт
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

        movement = Movement(movement_id=self._generate_id(), product_id=product_id,
            user_id=user_id, location_id=location_id, movement_type=movement_type, quantity=quantity, unit=unit,
            description=description, price=price, supplier_id=supplier_id, customer=customer, date=now, created=now, modified=now)

        self.movements.append(movement)
        self.save_changes()
        return movement

    def get_by_id(self, movement_id):
        # UUID е string - сравняваме като string
        movement_id = str(movement_id)
        return next((m for m in self.movements if str(m.movement_id) == movement_id),None)

    # IN / OUT движение
    def add(self, product_id: str, user_id: str, location_id: str, movement_type,
            quantity, description: str, price, customer: Optional[str] = None,
            supplier_id: Optional[str] = None) -> Movement:

        MovementValidator.validate_movement_type(movement_type)
        MovementValidator.validate_description(description)

        quantity = round(float(MovementValidator.parse_quantity(quantity)), 2)
        price = round(float(MovementValidator.parse_price(price)), 2)

        user, product = self._validate_user_and_product(user_id, product_id)

        # Преобразуване на movement_type, ако е подаден като число
        if isinstance(movement_type, int):
            mapping = {0: MovementType.IN, 1: MovementType.OUT, 2: MovementType.MOVE}
            movement_type = mapping.get(movement_type)
            if not movement_type:
                raise ValueError("Невалиден тип движение.")

        if movement_type == MovementType.MOVE:
            raise ValueError("MOVE може да се извършва само чрез move_product().")

        # IN движение
        if movement_type == MovementType.IN:
            product.quantity += quantity
            product.location_id = location_id
            if supplier_id is None:
                raise ValueError("При IN движение трябва да има доставчик.")
            action = "add"

        # OUT движение
        elif movement_type == MovementType.OUT:
            if product.quantity < quantity:
                raise ValueError("Недостатъчна наличност.")
            product.quantity -= quantity
            if not customer:
                raise ValueError("При OUT движение трябва да има клиент.")
            action = "remove"

        product.update_modified()
        self.product_controller.save_changes()

        movement = self._create_movement(product_id, user_id, location_id, movement_type,quantity,
                                         product.unit, description, price, supplier_id=supplier_id, customer=customer)

        # Логове
        self.stocklog_controller.add_log(product_id, location_id, quantity, product.unit, action)
        self._log_activity(user_id, movement_type, product, quantity, location_id)

        # Генериране на фактура при OUT
        if movement_type == MovementType.OUT:
            invoice = Invoice(movement_id=movement.movement_id, product=product.name, quantity=quantity, unit=product.unit,
                              unit_price=price, customer=customer)
            self.invoice_controller.add(invoice)

        return movement

    # MOVE – вътрешно преместване
    def move_product(self, product_id: str, user_id: str, from_location_id: str,
                     to_location_id: str, quantity: float, description: str = ""):

        if from_location_id == to_location_id:
            raise ValueError("MOVE трябва да е между различни локации.")

        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт {product_id} не съществува.")

        quantity = round(float(quantity), 2)

        if product.quantity < quantity:
            raise ValueError("Недостатъчна наличност за преместване.")

        # Обновяване на продукта
        product.location_id = to_location_id
        product.update_modified()
        self.product_controller.save_changes()

        # Създаване на движение
        move_entry = Movement(movement_id=self._generate_id(), product_id=product_id, user_id=user_id,
                              location_id=to_location_id,  # текуща локация
                              movement_type=MovementType.MOVE, quantity=quantity, unit=product.unit,
                              description=f"Преместване от {from_location_id} към {to_location_id}. {description}",
                              price=0, supplier_id=None, customer=None, from_location_id=from_location_id,
                              to_location_id=to_location_id, date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                              created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                              modified=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        self.movements.append(move_entry)
        self.save_changes()

        # Логове
        self.stocklog_controller.add_log(product_id, from_location_id, quantity, product.unit, "move_out")
        self.stocklog_controller.add_log(product_id, to_location_id, quantity, product.unit, "move_in")
        if self.activity_log:
            self.activity_log.add_log(user_id, "MOVE_PRODUCT", f"Moved {product.name} to {to_location_id}")
        return move_entry

    # Търсене по ключова дума (описание, продукт, клиент, доставчик)
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

            if (keyword in desc or keyword in product_name or keyword in movement_type or keyword in customer or
                    keyword in supplier):
                results.append(m)

        return results

    # Записване на промените
    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    # Връщане на всички движения
    def get_all(self) -> List[Movement]:
        return self.movements
