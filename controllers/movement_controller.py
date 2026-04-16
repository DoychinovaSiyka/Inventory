import uuid
from typing import Optional, List
from datetime import datetime

from models.movement import Movement, MovementType
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator
from filters.movement_filters import (filter_by_description, filter_advanced, filter_deliveries)


class MovementController:
    """ Контролер за управление на стоковите движения (IN, OUT, MOVE). Отговаря за координацията между
    моделите, валидаторите, инвентара, фактурите и логовете, без да съдържа бизнес логика. """

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

    # INTERNAL HELPERS

    def _load_movements(self) -> None:
        """Зарежда движенията от хранилището и ги преобразува в Movement обекти."""
        raw = self.repo.load() or []
        self.movements = [Movement.from_dict(m) for m in raw]

    @staticmethod
    def _now() -> str:
        """Връща текущата дата и час в стандартен формат."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _log(self, user_id: str, action: str, message: str) -> None:
        """Записва действие в системния лог, ако има активен лог контролер."""
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    def attach_supplier_controller(self, supplier_controller) -> None:
        """Позволява динамично закачане на контролер за доставчици."""
        self.supplier_controller = supplier_controller

    def check_movement_allowed(self, product_id: str, location_id: str, movement_type: str) -> None:
        """
        Предварителна проверка дали е допустимо да се извърши движение (IN/OUT)
        за даден продукт и локация, без да се променя инвентара.
        """
        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        MovementValidator.validate_movement_type(m_type_str)

        MovementValidator.validate_product_exists(product_id, self.product_controller)
        MovementValidator.validate_location_exists(location_id, self.location_controller)

        product = self.product_controller.get_by_id(product_id)
        MovementValidator.validate_location_rules(m_type_str, product, location_id)

    # --- IN / OUT (ВАРИАНТ 1: Inventory е единственият източник на истина) ---

    def add(self, product_id: str, user_id: str, location_id: str, movement_type: str,
            quantity: str, description: str, price: str, customer: Optional[str] = None,
            supplier_id: Optional[str] = None) -> Movement:

        # 1) Валидации
        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        MovementValidator.validate_movement_type(m_type_str)

        qty = MovementValidator.parse_quantity(quantity)
        prc = MovementValidator.parse_price(price)

        MovementValidator.validate_description(description)
        MovementValidator.validate_user_exists(user_id, self.user_controller)
        MovementValidator.validate_product_exists(product_id, self.product_controller)
        MovementValidator.validate_location_exists(location_id, self.location_controller)

        product = self.product_controller.get_by_id(product_id)

        # >>> НОВО: OUT проверява наличност от инвентара, не от product.quantity
        MovementValidator.validate_in_out_rules(
            m_type_str, product, qty, supplier_id, customer,
            self.inventory_controller, location_id
        )

        MovementValidator.validate_location_rules(m_type_str, product, location_id)

        # 2) Inventory операции — ЕДИНСТВЕНИЯТ източник на истина
        now = self._now()
        m_type_enum = MovementType[m_type_str]

        if m_type_enum == MovementType.IN:
            self.inventory_controller.increase_stock(product_id, product.name, location_id, qty)
            log_action = "add"

        elif m_type_enum == MovementType.OUT:
            self.inventory_controller.decrease_stock(product_id, location_id, qty)
            log_action = "remove"

        else:
            log_action = "none"

        # 3) Продуктът вече НЕ съдържа наличности.

        # 4) Създаване на движение
        movement = Movement(
            movement_id=str(uuid.uuid4()),
            product_id=product_id,
            user_id=user_id,
            location_id=location_id,
            movement_type=m_type_enum,
            quantity=qty,
            unit=product.unit,
            description=description,
            price=prc,
            supplier_id=supplier_id,
            customer=customer,
            date=now,
            created=now,
            modified=now
        )

        self.movements.append(movement)
        self.save_changes()

        # 5) Логове и фактури
        if log_action != "none":
            self.stocklog_controller.add_log(product_id, location_id, qty, product.unit, log_action)

        self._log(user_id, f"{m_type_str}_MOVEMENT", f"Product: {product.name}, Qty: {qty}")

        if m_type_enum == MovementType.OUT:
            self.invoice_controller.create_from_movement(movement, product, customer, user_id)

        return movement

    # MOVE
    def move_product(self, product_id: str, user_id: str, from_loc: str, to_loc: str,
                     quantity: str, description: str = "") -> Movement:

        qty = MovementValidator.parse_quantity(quantity)

        MovementValidator.validate_user_exists(user_id, self.user_controller)
        MovementValidator.validate_product_exists(product_id, self.product_controller)
        MovementValidator.validate_move_locations(from_loc, to_loc)
        MovementValidator.validate_location_exists(from_loc, self.location_controller)
        MovementValidator.validate_location_exists(to_loc, self.location_controller)
        MovementValidator.validate_move_stock(product_id, from_loc, qty, self.inventory_controller)

        product = self.product_controller.get_by_id(product_id)
        now = self._now()

        move_entry = Movement(
            movement_id=str(uuid.uuid4()),
            product_id=product_id,
            user_id=user_id,
            location_id=to_loc,
            movement_type=MovementType.MOVE,
            quantity=qty,
            unit=product.unit,
            description=f"От {from_loc} към {to_loc}. {description}",
            price=0,
            from_location_id=from_loc,
            to_location_id=to_loc,
            date=now,
            created=now,
            modified=now
        )

        self.movements.append(move_entry)
        self.save_changes()

        if self.inventory_controller:
            self.inventory_controller.move_stock(product_id, product.name, from_loc, to_loc, qty)

        self.stocklog_controller.add_log(product_id, from_loc, qty, product.unit, "move_out")
        self.stocklog_controller.add_log(product_id, to_loc, qty, product.unit, "move_in")
        self._log(user_id, "MOVE_PRODUCT", f"Moved {product.name} from {from_loc} to {to_loc}")

        return move_entry

    # READ / SEARCH

    def get_all(self) -> List[Movement]:
        return self.movements

    def get_by_id(self, m_id: str) -> Optional[Movement]:
        return next((m for m in self.movements if m.movement_id == m_id), None)

    def search_by_description(self, keyword: str) -> List[Movement]:
        return filter_by_description(self.movements, keyword)

    def search_delivery(self, keyword: str) -> List[Movement]:
        if not self.supplier_controller:
            return []
        return filter_deliveries(self.movements, keyword, self.product_controller, self.supplier_controller)

    def advanced_filter(self, **kwargs) -> List[Movement]:
        return filter_advanced(self.movements, **kwargs)

    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])
