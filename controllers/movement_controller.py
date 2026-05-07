from datetime import datetime
from typing import Optional, List
from models.movement import Movement, MovementType
from validators.movement_validator import MovementValidator


class MovementController:
    def __init__(self, repo, product_controller, user_controller, location_controller,
                 supplier_controller, invoice_controller, inventory_controller, activity_log_controller=None):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.invoice_controller = invoice_controller
        self.activity_log_controller = activity_log_controller
        self.inventory_controller = inventory_controller

        raw = self.repo.load() or []
        self.movements: List[Movement] = [Movement.from_dict(m) for m in raw]

    def save_changes(self) -> None:
        """Записва всички движения в базата данни (JSON)."""
        self.repo.save([m.to_dict() for m in self.movements])

    def add(self, product_id: str, user_id: str, location_id: Optional[str], movement_type: str,
            quantity: str, price: str, customer: Optional[str] = None, supplier_id: Optional[str] = None,
            from_location_id: Optional[str] = None, to_location_id: Optional[str] = None) -> Movement:

        # 1. Нормализация и базова валидация
        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        MovementValidator.validate_user_exists(user_id, self.user_controller)
        MovementValidator.validate_product_exists(product_id, self.product_controller)

        product = self.product_controller.get_by_id(product_id)
        qty = MovementValidator.parse_quantity(quantity)
        prc = MovementValidator.parse_price(price) if m_type_str != "MOVE" else 0.0

        # 2. Логика за локации (MOVE vs IN/OUT)
        if m_type_str == "MOVE":
            from_location_id = MovementValidator.validate_location_id(from_location_id, self.location_controller)
            to_location_id = MovementValidator.validate_location_id(to_location_id, self.location_controller)
            MovementValidator.validate_move_locations(from_location_id, to_location_id)
            MovementValidator.validate_move_stock(product_id, from_location_id, qty, self.inventory_controller)
        else:
            location_id = MovementValidator.validate_location_id(location_id, self.location_controller)

        # 3. Специфични правила за наличност
        MovementValidator.validate_in_out_rules(
            movement_type=m_type_str, product=product, quantity=qty,
            customer=customer, inventory_controller=self.inventory_controller,
            location_id=location_id if m_type_str != "MOVE" else from_location_id
        )

        # 4. Актуализиране на инвентара (Stock Update)
        if self.inventory_controller:
            if m_type_str == "IN":
                self.inventory_controller.increase_stock(product_id, qty, location_id)
            elif m_type_str == "OUT":
                self.inventory_controller.decrease_stock(product_id, qty, location_id)
            elif m_type_str == "MOVE":
                self.inventory_controller.decrease_stock(product_id, qty, from_location_id)
                self.inventory_controller.increase_stock(product_id, qty, to_location_id)

        # 5. СЪЗДАВАНЕ НА ОБЕКТА (ID-то се генерира автоматично в модела Movement)
        movement = Movement(
            movement_id=None,  # Вече не ползваме uuid.uuid4() тук!
            product_id=product_id,
            product_name=product.name,
            user_id=user_id,
            location_id=location_id if m_type_str != "MOVE" else None,
            movement_type=MovementType[m_type_str],
            quantity=qty,
            unit=product.unit,
            price=prc,
            supplier_id=supplier_id,
            customer=customer,
            from_location_id=from_location_id,
            to_location_id=to_location_id
        )

        self.movements.append(movement)
        self.save_changes()

        # 6. Логване на активност
        if self.activity_log_controller:
            self.activity_log_controller.log_action(
                user_id=user_id,
                action=f"MOVEMENT_{m_type_str}",
                details=f"Продукт: {product.name}, Кол: {qty} {product.unit}"
            )

        # 7. Автоматично генериране на фактура при продажба
        if m_type_str == "OUT" and self.invoice_controller:
            self.invoice_controller.create_from_movement(
                movement=movement,
                product=product,
                customer=customer or "Неизвестен клиент",
                user_id=user_id
            )

        return movement

    def advanced_filter(self, movement_type=None, start_date=None, end_date=None,
                        product_id=None, location_id=None, user_id=None):
        """Сложен филтър за справки."""
        results = []
        for m in self.movements:
            try:
                m_date = datetime.strptime(m.date[:10], "%Y-%m-%d")
            except:
                continue

            if movement_type and m.movement_type.name != movement_type:
                continue
            if start_date and m_date < start_date:
                continue
            if end_date and m_date > end_date:
                continue
            if product_id and str(m.product_id) != str(product_id):
                continue
            if user_id and str(m.user_id) != str(user_id):
                continue

            if location_id:
                if m.movement_type.name == "MOVE":
                    if m.from_location_id != location_id and m.to_location_id != location_id:
                        continue
                else:
                    if m.location_id != location_id:
                        continue

            results.append(m)
        return results