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

        # зареждаме движенията от json
        self.movements: List[Movement] = [Movement.from_dict(m) for m in self.repo.load()]

    # id generator – оперативен запис
    def _generate_id(self) -> int:
        if not self.movements: return 1
        return max(m.movement_id for m in self.movements) + 1

    def add(self, product_id: str, user_id: str, location_id: int, movement_type,
            quantity, description: str, price, customer: Optional[str] = None,
            supplier_id: Optional[str] = None) -> Movement:

        action = None

        # валидации
        MovementValidator.validate_movement_type(movement_type)
        MovementValidator.validate_description(description)

        quantity = MovementValidator.parse_quantity(quantity)
        price = MovementValidator.parse_price(price)

        # потребител
        user = next((u for u in self.user_controller.users if u.user_id == user_id), None)
        if not user: raise ValueError(f"Потребител с ID {user_id} не съществува.")

        # продукт
        product = next((p for p in self.product_controller.products
                        if p.product_id == product_id), None)
        if not product: raise ValueError(f"Продукт с ID {product_id} не съществува.")

        # локация
        location = next((l for l in self.location_controller.locations
                         if l.location_id == location_id), None)
        if not location: raise ValueError(f"Локация с ID {location_id} не съществува.")

        # преобразуване на movement_type
        if isinstance(movement_type, int):
            mapping = {0: MovementType.IN, 1: MovementType.OUT, 2: MovementType.MOVE}
            if movement_type not in mapping: raise ValueError("Невалиден тип движение.")
            movement_type = mapping[movement_type]

        # забраняваме move през add()
        if movement_type == MovementType.MOVE:
            raise ValueError("MOVE може да се извършва само чрез move_product().")

        # бизнес логика
        if movement_type == MovementType.IN:
            product.quantity += quantity; action = "add"
            if supplier_id is None: raise ValueError("При IN движение трябва да има доставчик.")

        elif movement_type == MovementType.OUT:
            if product.quantity < quantity: raise ValueError("Недостатъчна наличност.")
            product.quantity -= quantity; action = "remove"
            if not customer: raise ValueError("При OUT движение трябва да има клиент.")

        # обновяване на продукта
        product.update_modified(); self.product_controller.save_changes()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        movement = Movement(
            movement_id=self._generate_id(), product_id=product_id, user_id=user_id,
            location_id=location_id, movement_type=movement_type, quantity=quantity,
            unit=product.unit, description=description, price=price,supplier_id=supplier_id,
            customer=customer, date=now,created=now, modified=now)

        self.movements.append(movement); self.save_changes()

        # stocklog
        self.stocklog_controller.add_log(product_id=product_id, location_id=location_id,
                                         quantity=quantity, unit=product.unit, action=action)

        # activity log
        if self.activity_log:
            if movement_type == MovementType.IN:
                self.activity_log.add_log(user_id, "IN_MOVEMENT",
                    f"IN movement: product {product_id}, qty={quantity}, "
                    f"loc={location_id}, supplier={supplier_id}")
            elif movement_type == MovementType.OUT:
                self.activity_log.add_log(user_id, "OUT_MOVEMENT",
                    f"OUT movement: product {product_id}, qty={quantity}, "
                    f"loc={location_id}, customer={customer}")

        # фактура при OUT
        if movement_type == MovementType.OUT:
            invoice = Invoice(movement_id=movement.movement_id, product=product.name,
                              quantity=quantity, unit=product.unit, unit_price=price,
                              customer=customer)
            self.invoice_controller.add(invoice)

        return movement

    # move — с две движения
    def move_product(self, product_id: str, user_id: str, from_location_id: int,
                     to_location_id: int, quantity: float, description: str = ""):

        if from_location_id == to_location_id:
            raise ValueError("MOVE трябва да е между различни локации.")

        user = next((u for u in self.user_controller.users if u.user_id == user_id), None)
        if not user: raise ValueError(f"Потребител {user_id} не съществува.")

        product = next((p for p in self.product_controller.products
                        if p.product_id == product_id), None)
        if not product: raise ValueError(f"Продукт {product_id} не съществува.")

        from_loc = next((l for l in self.location_controller.locations
                         if l.location_id == from_location_id), None)
        to_loc = next((l for l in self.location_controller.locations
                       if l.location_id == to_location_id), None)

        if not from_loc: raise ValueError(f"Изходна локация {from_location_id} не съществува.")
        if not to_loc: raise ValueError(f"Целева локация {to_location_id} не съществува.")

        if product.quantity < quantity:
            raise ValueError("Недостатъчна наличност за преместване.")

        # move out
        out_movement = Movement(
            movement_id=self._generate_id(), product_id=product_id, user_id=user_id,
            location_id=from_location_id, movement_type=MovementType.MOVE,
            quantity=quantity, unit=product.unit,
            description=f"Преместване от {from_location_id} → {to_location_id}. {description}",
            price=0, customer=None, supplier_id=None,
            from_location_id=from_location_id, to_location_id=to_location_id)

        # move in
        in_movement = Movement(movement_id=self._generate_id(), product_id=product_id, user_id=user_id,
            location_id=to_location_id, movement_type=MovementType.MOVE,
            quantity=quantity, unit=product.unit,
            description=f"Преместване към {to_location_id} ← {from_location_id}. {description}",
            price=0, customer=None, supplier_id=None,
            from_location_id=from_location_id, to_location_id=to_location_id)

        # количества
        product.quantity -= quantity; product.quantity += quantity
        product.update_modified(); self.product_controller.save_changes()

        # запис
        self.movements.append(out_movement); self.movements.append(in_movement)
        self.save_changes()

        # stocklog
        self.stocklog_controller.add_log(product_id=product_id, location_id=from_location_id,
                                         quantity=quantity, unit=product.unit, action="move")
        self.stocklog_controller.add_log(product_id=product_id, location_id=to_location_id,
                                         quantity=quantity, unit=product.unit, action="move")

        # activity log
        if self.activity_log:
            self.activity_log.add_log(user_id, "MOVE_PRODUCT",
                f"Moved product {product_id} from {from_location_id} to {to_location_id}, "
                f"qty={quantity}")

        return out_movement, in_movement

    # филтри
    def filter_by_type(self, movement_type) -> List[Movement]:
        return [m for m in self.movements if m.movement_type == movement_type]

    def filter_by_date_range(self, start_date: str = None, end_date: str = None) -> List[Movement]:
        results = self.movements

        def parse(d):
            try: return datetime.strptime(d, "%Y-%m-%d")
            except: return None

        start = parse(start_date) if start_date else None
        end = parse(end_date) if end_date else None

        if start:
            results = [m for m in results if datetime.strptime(m.date[:10],
                                                               "%Y-%m-%d") >= start]
        if end:
            results = [m for m in results if datetime.strptime(m.date[:10],
                                                               "%Y-%m-%d") <= end]

        return results

    def filter_by_product(self, product_id: str) -> List[Movement]:
        return [m for m in self.movements if m.product_id == product_id]

    def filter_by_location(self, location_id: int) -> List[Movement]:
        return [m for m in self.movements if m.location_id == location_id]

    def filter_by_user(self, user_id: str) -> List[Movement]:
        return [m for m in self.movements if m.user_id == user_id]

    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    def get_all(self) -> List[Movement]:
        return self.movements

    def search(self, keyword: str) -> List[Movement]:
        keyword = keyword.lower()
        return [m for m in self.movements if keyword in (m.description or "").lower()]
