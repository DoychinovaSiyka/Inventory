import uuid
from typing import Optional, List
from models.movement import Movement, MovementType
from validators.movement_validator import MovementValidator


class MovementController:
    def __init__(self, repo, product_controller, user_controller, location_controller,
                 invoice_controller, activity_log_controller=None, inventory_controller=None, supplier_controller=None):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.invoice_controller = invoice_controller
        self.activity_log_controller = activity_log_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller

        self.movements = self._load_movements()

    def _load_movements(self) -> List[Movement]:
        raw = self.repo.load() or []
        return [Movement.from_dict(m) for m in raw]

    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    def add(self, product_id: str, user_id: str, location_id: Optional[str], movement_type: str,
            quantity: str, description: str, price: str, customer: Optional[str] = None,
            supplier_id: Optional[str] = None, from_location_id: Optional[str] = None,
            to_location_id: Optional[str] = None) -> Movement:

        # Нормализиране на типа движение
        m_type_str = MovementValidator.normalize_movement_type(movement_type)

        # Проверка за продукт
        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не е намерен.")

        qty = MovementValidator.parse_quantity(quantity)
        prc = MovementValidator.parse_price(price) if m_type_str != "MOVE" else 0.0

        # --- ОБНОВЯВАНЕ НА ИНВЕНТАРА ---
        if self.inventory_controller:
            if m_type_str == "IN":
                self.inventory_controller.increase_stock(product_id, qty, location_id)

            elif m_type_str == "OUT":
                self.inventory_controller.decrease_stock(product_id, qty, location_id)

            elif m_type_str == "MOVE":
                self.inventory_controller.decrease_stock(product_id, qty, from_location_id)
                self.inventory_controller.increase_stock(product_id, qty, to_location_id)

        # --- СЪЗДАВАНЕ НА ДВИЖЕНИЕ ---
        movement = Movement(
            movement_id=str(uuid.uuid4()),
            product_id=product_id,
            product_name=product.name,
            user_id=user_id,
            location_id=location_id if m_type_str != "MOVE" else None,
            movement_type=MovementType[m_type_str],
            quantity=qty,
            unit=product.unit,
            description=description,
            price=prc,
            supplier_id=product.supplier_id,
            customer=customer,
            from_location_id=from_location_id,
            to_location_id=to_location_id
        )

        self.movements.append(movement)
        self.save_changes()

        # --- СЪЗДАВАНЕ НА ФАКТУРА ПРИ OUT ---
        if m_type_str == "OUT" and self.invoice_controller:
            self.invoice_controller.create_from_movement(
                movement=movement,
                product=product,
                customer=customer or "Неизвестен клиент",
                user_id=user_id
            )

        return movement
