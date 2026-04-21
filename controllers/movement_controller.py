import uuid
from typing import Optional, List
from datetime import datetime
from models.movement import Movement, MovementType
from storage.json_repository import JSONRepository
from validators.movement_validator import MovementValidator
from filters.movement_filters import filter_by_description, filter_advanced


class MovementController:
    """Контролер за движенията. Оправен да не презаписва излишно."""

    def __init__(self, repo: JSONRepository, product_controller, user_controller,
                 location_controller, invoice_controller, activity_log_controller=None,
                 inventory_controller=None, supplier_controller=None):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.invoice_controller = invoice_controller
        self.activity_log = activity_log_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller

        self.movements: List[Movement] = []
        self._load_movements()

        # Инвентарът ще се преизчислява само в паметта.
        self._sync_inventory_only_in_memory()

    def _load_movements(self) -> None:
        raw = self.repo.load() or []
        self.movements = [Movement.from_dict(m) for m in raw]

    def _sync_inventory_only_in_memory(self) -> None:
        """Обновява инвентара в RAM паметта без да записва във файловете."""
        if not self.inventory_controller:
            return

        safe_movements = self._inventory_safe_movements()
        safe_movements.sort(key=lambda m: m.date)
        try:
            # Rebuild само в паметта
            self.inventory_controller.rebuild_inventory_from_movements(safe_movements)
        except Exception:
            pass

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def save_changes(self) -> None:
        """Записва на диска само при реална промяна."""
        self.repo.save([m.to_dict() for m in self.movements])

    def _inventory_safe_movements(self) -> List[Movement]:
        safe = []
        for m in self.movements:
            if self.product_controller.get_by_id(m.product_id):
                safe.append(m)
        return safe

    def add(self, product_id: str, user_id: str, location_id: Optional[str], movement_type: str, quantity: str,
            description: str, price: str, customer: Optional[str] = None, supplier_id: Optional[str] = None,
            from_location_id: Optional[str] = None, to_location_id: Optional[str] = None) -> Movement:

        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        MovementValidator.validate_movement_type(m_type_str)
        qty = MovementValidator.parse_quantity(quantity)

        prc = None if m_type_str == "MOVE" else MovementValidator.parse_price(price)

        product = self.product_controller.get_by_id(product_id)

        # Логика за движение...
        if m_type_str == "MOVE":
            self.inventory_controller.decrease_stock(product_id, from_location_id, qty, product.unit)
            self.inventory_controller.increase_stock(product_id, product.name, to_location_id, qty, product.unit)
            location_id = None
        else:
            if m_type_str == "IN":
                self.inventory_controller.increase_stock(product_id, product.name, location_id, qty, product.unit)
            elif m_type_str == "OUT":
                self.inventory_controller.decrease_stock(product_id, location_id, qty, product.unit)

        now = self._now()
        movement = Movement(movement_id=str(uuid.uuid4()), product_id=product_id, product_name=product.name,
                            user_id=user_id, location_id=location_id, movement_type=MovementType[m_type_str],
                            quantity=qty, unit=product.unit, description=description, price=prc,
                            supplier_id=supplier_id, customer=customer, date=now, created=now, modified=now)

        self.movements.append(movement)

        # ЗАПИСВАМЕ ПРИ НОВО ДВИЖЕНИЕ
        self.save_changes()

        if MovementType[m_type_str] == MovementType.OUT:
            self.invoice_controller.create_from_movement(movement, product, customer, user_id)

        return movement


    def rebuild_inventory(self) -> None:
        """Ръчно преизчисляване на всичко."""
        if not self.inventory_controller:
            return
        safe_movements = self._inventory_safe_movements()
        safe_movements.sort(key=lambda m: m.date)
        self.inventory_controller.rebuild_inventory_from_movements(safe_movements)