import uuid
from typing import Optional, List
from datetime import datetime

from models.movement import Movement, MovementType
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator
from filters.movement_filters import filter_by_description, filter_advanced


class MovementController:
    """
    Контролер за управление на стоковите движения (IN, OUT, MOVE).

    Архитектурен принцип:
    - Истината за наличностите е в movements.json (IN/OUT/MOVE).
    - inventory.json е производен файл и се пресмята от движенията.
    - Няма начални количества без произход (без IN движение).
    """

    def __init__(self,
                 repo: JSONRepository,
                 product_controller,
                 user_controller,
                 location_controller,
                 stocklog_controller,
                 invoice_controller,
                 activity_log_controller=None,
                 inventory_controller=None,
                 supplier_controller=None):

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
        self._sync_inventory_from_movements()

    # ---------------------------------------------------------
    # LOAD
    # ---------------------------------------------------------
    def _load_movements(self) -> None:
        raw = self.repo.load() or []
        self.movements = [Movement.from_dict(m) for m in raw]

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _log(self, user_id: str, action: str, message: str) -> None:
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    # ---------------------------------------------------------
    # INVENTORY SYNC
    # ---------------------------------------------------------
    def _inventory_safe_movements(self) -> List[Movement]:
        safe = []
        for m in self.movements:
            if self.product_controller.get_by_id(m.product_id):
                safe.append(m)
        return safe

    def _sync_inventory_from_movements(self) -> None:
        if not self.inventory_controller:
            return

        # 1) Генерира IN за продукти с OUT, но без IN
        self._generate_initial_in_movements()

        # 2) Генерира IN за продукти без НИКАКВИ движения
        self.generate_initial_stock_for_all_products()

        safe_movements = self._inventory_safe_movements()
        safe_movements.sort(key=lambda m: m.date)

        try:
            self.inventory_controller.rebuild_inventory_from_movements(safe_movements)
        except Exception:
            pass

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------
    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    # ---------------------------------------------------------
    # BASIC GETTERS
    # ---------------------------------------------------------
    def get_by_id(self, movement_id):
        for m in self.movements:
            if m.movement_id == movement_id:
                return m
        return None

    # ---------------------------------------------------------
    # VALIDATION HELPERS
    # ---------------------------------------------------------
    def check_movement_allowed(self, product_id: str, location_id: str, movement_type: str) -> bool:
        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не съществува.")

        if not self.inventory_controller:
            return True

        if movement_type.upper() == "OUT":
            current_qty = self.inventory_controller.get_stock_for_location(product_id, location_id)
            if current_qty <= 0:
                raise ValueError("Нулева наличност в избрания склад!")

        return True

    # ---------------------------------------------------------
    # ADD MOVEMENT (IN / OUT)
    # ---------------------------------------------------------
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

        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        MovementValidator.validate_movement_type(m_type_str)

        qty = MovementValidator.parse_quantity(quantity)
        input_price = MovementValidator.parse_price(price)

        MovementValidator.validate_description(description)
        MovementValidator.validate_user_exists(user_id, self.user_controller)
        MovementValidator.validate_product_exists(product_id, self.product_controller)
        MovementValidator.validate_location_exists(location_id, self.location_controller)

        product = self.product_controller.get_by_id(product_id)

        MovementValidator.validate_in_out_rules(
            m_type_str, product, qty, supplier_id, customer,
            self.inventory_controller, location_id
        )

        now = self._now()
        m_type_enum = MovementType[m_type_str]

        # Цена
        if m_type_enum == MovementType.OUT:
            prc = float(product.price)
        else:
            prc = input_price

        # Инвентар
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

        if log_action != "none":
            self.stocklog_controller.add_log(product_id, location_id, qty, product.unit, log_action)

        self._log(user_id, f"{m_type_str}_MOVEMENT", f"Product: {product.name}, Qty: {qty}, Price: {prc}")

        if m_type_enum == MovementType.OUT:
            self.invoice_controller.create_from_movement(movement, product, customer, user_id)

        return movement

    # ---------------------------------------------------------
    # MOVE
    # ---------------------------------------------------------
    def move_product(self,
                     product_id: str,
                     user_id: str,
                     from_loc: str,
                     to_loc: str,
                     quantity: str,
                     description: str = "") -> Movement:

        qty = MovementValidator.parse_quantity(quantity)

        MovementValidator.validate_user_exists(user_id, self.user_controller)
        MovementValidator.validate_product_exists(product_id, self.product_controller)
        MovementValidator.validate_move_locations(from_loc, to_loc)
        MovementValidator.validate_location_exists(from_loc, self.location_controller)
        MovementValidator.validate_location_exists(to_loc, self.location_controller)
        MovementValidator.validate_move_stock(product_id, from_loc, qty, self.inventory_controller)

        product = self.product_controller.get_by_id(product_id)
        now = self._now()

        if self.inventory_controller:
            self.inventory_controller.move_stock(
                product_id, product.name, from_loc, to_loc, qty, product.unit
            )

        loc_from_obj = self.location_controller.get_by_id(from_loc)
        loc_to_obj = self.location_controller.get_by_id(to_loc)

        name_from = loc_from_obj.name if loc_from_obj else from_loc
        name_to = loc_to_obj.name if loc_to_obj else to_loc

        move_entry = Movement(
            movement_id=str(uuid.uuid4()),
            product_id=product_id,
            product_name=product.name,
            user_id=user_id,
            location_id=to_loc,
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

    # ---------------------------------------------------------
    # AUTO INITIAL IN (ако има OUT, но няма IN)
    # ---------------------------------------------------------
    def _generate_initial_in_movements(self):
        if not self.inventory_controller:
            return

        product_movements = {}
        for m in self.movements:
            product_movements.setdefault(m.product_id, []).append(m)

        new_movements = []

        for product_id, moves in product_movements.items():
            has_in = any(m.movement_type == MovementType.IN for m in moves)
            outs = [m for m in moves if m.movement_type == MovementType.OUT]

            if has_in or not outs:
                continue

            total_out_qty = sum(m.quantity for m in outs)
            earliest_date = min(m.date for m in outs)

            product = self.product_controller.get_by_id(product_id)
            if not product:
                continue

            all_locations = self.location_controller.get_all()
            if not all_locations:
                continue

            default_location = all_locations[0].location_id

            auto_in = Movement(
                movement_id=str(uuid.uuid4()),
                product_id=product_id,
                product_name=product.name,
                user_id="system",
                location_id=default_location,
                movement_type=MovementType.IN,
                quantity=total_out_qty,
                unit=product.unit,
                description="Автоматично начално зареждане",
                price=float(product.price),
                supplier_id=None,
                customer=None,
                date=earliest_date,
                created=earliest_date,
                modified=earliest_date
            )

            new_movements.append(auto_in)

        if new_movements:
            self.movements.extend(new_movements)
            self.movements.sort(key=lambda m: m.date)
            self.repo.save([m.to_dict() for m in self.movements])

    # ---------------------------------------------------------
    # AUTO INITIAL IN (ако продуктът няма НИКАКВИ движения)
    # ---------------------------------------------------------
    def generate_initial_stock_for_all_products(self):
        """Създава начално IN движение за всеки продукт, който няма никакви движения."""

        if not self.inventory_controller:
            return

        products = self.product_controller.get_all()
        product_ids_with_moves = {m.product_id for m in self.movements}

        all_locations = self.location_controller.get_all()
        if not all_locations:
            return

        default_location = all_locations[0].location_id

        new_movements = []

        for p in products:
            if p.product_id in product_ids_with_moves:
                continue  # продуктът вече има движения

            qty = 50  # начално количество
            now = self._now()

            auto_in = Movement(
                movement_id=str(uuid.uuid4()),
                product_id=p.product_id,
                product_name=p.name,
                user_id="system",
                location_id=default_location,
                movement_type=MovementType.IN,
                quantity=qty,
                unit=p.unit,
                description="Начално зареждане (автоматично)",
                price=float(p.price),
                supplier_id=None,
                customer=None,
                date=now,
                created=now,
                modified=now
            )

            new_movements.append(auto_in)

        if new_movements:
            self.movements.extend(new_movements)
            self.save_changes()

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------
    def search_by_description(self, keyword: str):
        return filter_by_description(self.movements, keyword)

    def advanced_filter(self, **kwargs):
        return filter_advanced(self.movements, **kwargs)

    # ---------------------------------------------------------
    # REBUILD
    # ---------------------------------------------------------
    def rebuild_inventory(self) -> None:
        if not self.inventory_controller:
            raise ValueError("InventoryController не е инициализиран.")

        self._generate_initial_in_movements()
        self.generate_initial_stock_for_all_products()

        safe_movements = self._inventory_safe_movements()
        safe_movements.sort(key=lambda m: m.date)
        self.inventory_controller.rebuild_inventory_from_movements(safe_movements)
