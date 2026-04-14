import uuid
from typing import Optional, List
from datetime import datetime
from models.movement import Movement, MovementType
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator

# Всички филтри отиват тук
from filters.movement_filters import (filter_by_description, filter_advanced, filter_deliveries)


class MovementController:
    def __init__(self, repo: JSONRepository, product_controller, user_controller,
                 location_controller, stocklog_controller, invoice_controller,
                 activity_log_controller=None, inventory_controller=None, supplier_controller=None):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.stocklog_controller = stocklog_controller
        self.invoice_controller = invoice_controller
        self.activity_log = activity_log_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller

        self.movements: List[Movement] = []
        self._load_movements()

    def _load_movements(self):
        raw = self.repo.load()
        self.movements = [Movement.from_dict(m) for m in raw]

    def _get_now(self):
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _log(self, user_id, action, message):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    # --- ТОВА Е МЕТОДЪТ, КОЙТО ОПРАВЯ ГРЕШКАТА В MAIN.PY ---
    def attach_supplier_controller(self, supplier_controller):
        """ Свързва контролера за доставчици, ако не е подаден при инициализацията. """
        self.supplier_controller = supplier_controller

    # CREATE (IN / OUT)
    def add(self, product_id: str, user_id: str, location_id: str, movement_type: str,
            quantity: str, description: str, price: str, customer: Optional[str] = None,
            supplier_id: Optional[str] = None) -> Movement:

        # 1. Валидация и подготовка на данните
        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        MovementValidator.validate_movement_type(m_type_str)
        m_type_enum = MovementType[m_type_str]

        qty = MovementValidator.parse_quantity(quantity)
        prc = MovementValidator.parse_price(price)
        MovementValidator.validate_description(description)

        product = self.product_controller.get_by_id(product_id)
        MovementValidator.validate_product_exists(product_id, self.product_controller)
        MovementValidator.validate_in_out_rules(m_type_str, product, qty, supplier_id, customer)

        # 2. Логика за наличност (Stock Management)
        now = self._get_now()
        if m_type_enum == MovementType.IN:
            product.quantity += qty
            product.location_id = location_id
            if self.inventory_controller:
                self.inventory_controller.increase_stock(product_id, product.name, location_id, qty)
            log_action = "add"
        else:
            product.quantity -= qty
            if self.inventory_controller:
                self.inventory_controller.decrease_stock(product_id, location_id, qty)
            log_action = "remove"

        product.update_modified()
        self.product_controller.save_changes()

        # 3. Създаване на запис за движение
        movement = Movement(
            movement_id=str(uuid.uuid4()), product_id=product_id, user_id=user_id,
            location_id=location_id, movement_type=m_type_enum, quantity=qty,
            unit=product.unit, description=description, price=prc,
            supplier_id=supplier_id, customer=customer, date=now, created=now, modified=now
        )

        self.movements.append(movement)
        self.save_changes()

        # 4. Външни логвания и фактури
        self.stocklog_controller.add_log(product_id, location_id, qty, product.unit, log_action)
        self._log(user_id, f"{m_type_str}_MOVEMENT", f"Product: {product.name}, Qty: {qty}")

        if m_type_enum == MovementType.OUT:
            self.invoice_controller.create_from_movement(movement, product, customer, user_id)

        return movement

    # MOVE (Преместване)
    def move_product(self, product_id: str, user_id: str, from_loc: str, to_loc: str,
                     quantity: str, description: str = "") -> Movement:

        MovementValidator.validate_move_locations(from_loc, to_loc)
        qty = MovementValidator.parse_quantity(quantity)
        product = self.product_controller.get_by_id(product_id)

        MovementValidator.validate_move_stock(product_id, from_loc, qty, self.inventory_controller)

        now = self._get_now()
        move_entry = Movement(
            movement_id=str(uuid.uuid4()), product_id=product_id, user_id=user_id,
            location_id=to_loc, movement_type=MovementType.MOVE, quantity=qty,
            unit=product.unit, description=f"От {from_loc} към {to_loc}. {description}",
            price=0, from_location_id=from_loc, to_location_id=to_loc,
            date=now, created=now, modified=now
        )

        self.movements.append(move_entry)
        self.save_changes()

        self.inventory_controller.move_stock(product_id, product.name, from_loc, to_loc, qty)
        self.stocklog_controller.add_log(product_id, from_loc, qty, product.unit, "move_out")
        self.stocklog_controller.add_log(product_id, to_loc, qty, product.unit, "move_in")
        self._log(user_id, "MOVE_PRODUCT", f"Moved {product.name} from {from_loc} to {to_loc}")

        return move_entry

    def check_movement_allowed(self, product_id, location_id, movement_type):
        # Проверка дали продуктът съществува
        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не е намерен.")

        # Проверка дали локацията съществува
        location = self.location_controller.get_by_id(location_id)
        if not location:
            raise ValueError("Локацията не е намерена.")

        # Забрана за доставка до същата локация
        if movement_type == "IN":
            if product.location_id == location_id:
                raise ValueError("Не може да доставяте продукт в същата локация, в която вече се намира.")

        # Проверка за наличност при OUT
        if movement_type == "OUT":
            stock_qty = self.inventory_controller.get_quantity(product_id, location_id)
            if stock_qty is None or stock_qty <= 0:
                raise ValueError("Няма наличност от този продукт в избраната локация.")

    # READ / SEARCH (Изнесени във филтрите)
    def get_all(self) -> List[Movement]:
        return self.movements

    def get_by_id(self, m_id: str) -> Optional[Movement]:
        return next((m for m in self.movements if str(m.movement_id) == str(m_id)), None)

    def search_by_description(self, keyword: str):
        return filter_by_description(self.movements, keyword)

    def search_delivery(self, keyword: str) -> List[Movement]:
        return filter_deliveries(self.movements, keyword, self.product_controller, self.supplier_controller)

    def advanced_filter(self, **kwargs):
        return filter_advanced(self.movements, **kwargs)

    def save_changes(self):
        self.repo.save([m.to_dict() for m in self.movements])