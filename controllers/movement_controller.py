import uuid
from typing import Optional, List
from datetime import datetime

from models.movement import Movement, MovementType
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator
from filters.movement_filters import filter_by_description, filter_advanced

class MovementController:
    """Контролер за управление на стоковите движения (IN, OUT, MOVE)."""

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

    # ================== INTERNAL HELPERS ==================

    def _load_movements(self) -> None:
        raw = self.repo.load() or []
        self.movements = [Movement.from_dict(m) for m in raw]

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _log(self, user_id: str, action: str, message: str) -> None:
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    def get_by_id(self, movement_id):
        for m in self.movements:
            if m.movement_id == movement_id:
                return m
        return None

    # ================== CHECKS ==================

    def check_movement_allowed(self, product_id: str, location_id: str, movement_type: str) -> bool:
        """Бърза проверка дали движението е допустимо спрямо наличностите."""
        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не съществува.")

        if not self.inventory_controller:
            return True

        mt = movement_type.upper()
        if mt == "OUT":
            current_qty = self.inventory_controller.get_stock_for_location(product_id, location_id)
            if current_qty <= 0:
                raise ValueError("Нулева наличност в избрания склад!")

        return True

    # ================== IN / OUT ==================

    def add(self,
            product_id: str,
            user_id: str,
            location_id: str,
            movement_type: str,
            quantity: str,
            description: str,
            price: str,
            customer: Optional[str] = None,
            supplier_id: Optional[str] = None) -> Movement:
        """
        Създава IN или OUT движение.
        При OUT по подразбиране използва каталожната цена на продукта,
        а въведената цена може да бъде валидирана/ограничена.
        """

        # 1) Нормализиране и базови валидации
        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        MovementValidator.validate_movement_type(m_type_str)

        qty = MovementValidator.parse_quantity(quantity)
        input_price = MovementValidator.parse_price(price)

        MovementValidator.validate_description(description)
        MovementValidator.validate_user_exists(user_id, self.user_controller)
        MovementValidator.validate_product_exists(product_id, self.product_controller)
        MovementValidator.validate_location_exists(location_id, self.location_controller)

        product = self.product_controller.get_by_id(product_id)

        # 2) Бизнес правила за IN/OUT (наличности, доставчик, клиент и т.н.)
        MovementValidator.validate_in_out_rules(
            m_type_str, product, qty, supplier_id, customer,
            self.inventory_controller, location_id
        )

        MovementValidator.validate_location_rules(m_type_str, product, location_id)

        now = self._now()
        m_type_enum = MovementType[m_type_str]

        # 3) ЦЕНОВА ЛОГИКА
        # При IN: цената е доставна (input_price).
        # При OUT: по подразбиране използваме каталожната цена на продукта.
        if m_type_enum == MovementType.OUT:
            catalog_price = float(product.price)
            # ако искаш да позволиш override, тук може да се сложи проверка за диапазон
            # MovementValidator.validate_sale_price(input_price, catalog_price)
            prc = catalog_price
        else:
            prc = input_price

        # 4) ОПЕРАЦИИ ВЪРХУ ИНВЕНТАРА
        if self.inventory_controller:
            if m_type_enum == MovementType.IN:
                self.inventory_controller.increase_stock(
                    product_id, product.name, location_id, qty, product.unit
                )
                log_action = "add"

            elif m_type_enum == MovementType.OUT:
                current_stock = self.inventory_controller.get_stock_for_location(product_id, location_id)
                if current_stock < qty:
                    raise ValueError(
                        f"Недостатъчна наличност! Налично: {current_stock} {product.unit}, Търсено: {qty}"
                    )

                self.inventory_controller.decrease_stock(
                    product_id, location_id, qty, product.unit
                )
                log_action = "remove"
            else:
                log_action = "none"
        else:
            log_action = "none"

        # 5) СЪЗДАВАНЕ НА ЗАПИС ЗА ДВИЖЕНИЕТО
        movement = Movement(
            movement_id=str(uuid.uuid4()),
            product_id=product_id,
            product_name=product.name,
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

        # 6) ЛОГВАНЕ + ФАКТУРА
        if log_action != "none":
            self.stocklog_controller.add_log(product_id, location_id, qty, product.unit, log_action)

        self._log(user_id, f"{m_type_str}_MOVEMENT", f"Product: {product.name}, Qty: {qty}, Price: {prc}")

        if m_type_enum == MovementType.OUT:
            self.invoice_controller.create_from_movement(movement, product, customer, user_id)

        return movement

    #  MOVE ==================

    def move_product(self,
                     product_id: str,
                     user_id: str,
                     from_loc: str,
                     to_loc: str,
                     quantity: str,
                     description: str = "") -> Movement:
        """
        MOVE: прехвърля наличност между два склада.
        Не променя общата наличност, само разпределението по локации.
        """

        qty = MovementValidator.parse_quantity(quantity)

        MovementValidator.validate_user_exists(user_id, self.user_controller)
        MovementValidator.validate_product_exists(product_id, self.product_controller)
        MovementValidator.validate_move_locations(from_loc, to_loc)
        MovementValidator.validate_location_exists(from_loc, self.location_controller)
        MovementValidator.validate_location_exists(to_loc, self.location_controller)
        MovementValidator.validate_move_stock(product_id, from_loc, qty, self.inventory_controller)

        product = self.product_controller.get_by_id(product_id)
        now = self._now()

        # 1) ОБНОВЯВАНЕ НА ИНВЕНТАРА
        if self.inventory_controller:
            self.inventory_controller.move_stock(
                product_id, product.name, from_loc, to_loc, qty, product.unit
            )

        # 2) СЪЗДАВАНЕ НА MOVE ЗАПИС
        loc_from_obj = self.location_controller.get_by_id(from_loc)
        loc_to_obj = self.location_controller.get_by_id(to_loc)

        name_from = loc_from_obj.name if loc_from_obj else from_loc
        name_to = loc_to_obj.name if loc_to_obj else to_loc

        move_entry = Movement(
            movement_id=str(uuid.uuid4()),
            product_id=product_id,
            product_name=product.name,
            user_id=user_id,
            location_id=to_loc,          # целевата локация
            movement_type=MovementType.MOVE,
            quantity=qty,
            unit=product.unit,
            description=f"Трансфер: {name_from} -> {name_to}. {description}",
            price=0,
            from_location_id=from_loc,
            to_location_id=to_loc,
            date=now,
            created=now,
            modified=now
        )

        self.movements.append(move_entry)
        self.save_changes()

        self._log(user_id, "MOVE_MOVEMENT",
                  f"Product: {product.name}, Qty: {qty}, From: {name_from}, To: {name_to}")

        return move_entry

    def search_by_description(self, keyword: str):
        """Контролерът подава своите данни на външния филтър."""
        return filter_by_description(self.movements, keyword)

    def advanced_filter(self, **kwargs):
        """Контролерът подава всичко на разширения филтър."""
        return filter_advanced(self.movements, **kwargs)
    # ================== ПРЕСМЯТАНЕ НА ИНВЕНТАРА ОТ movements.json ==================

    def rebuild_inventory(self) -> None:
        """
        Извиква rebuild_inventory_from_movements() в InventoryController.
        Това пресмята целия инвентар от movements.json.
        """
        if not self.inventory_controller:
            raise ValueError("InventoryController не е инициализиран.")

        self.inventory_controller.rebuild_inventory_from_movements(self.movements)
