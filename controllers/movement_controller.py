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

    def get_all(self) -> List[Movement]:
        """Връща списък с всички движения."""
        return self.movements

    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    def add_in(self, product_id, quantity, price, location_id, supplier_id, user_id):
        return self.add(product_id, user_id, location_id, "IN", quantity, price, supplier_id=supplier_id)

    def add_out(self, product_id, quantity, customer, location_id, user_id):
        current_stock = self.inventory_controller.get_stock_by_location(product_id, location_id)
        if current_stock < float(quantity):
            raise ValueError(f"Недостатъчна наличност в този склад! Налично: {current_stock}, Искано: {quantity}")

        return self.add(product_id, user_id, location_id, "OUT", quantity, None, customer=customer)

    def move_stock(self, product_id, quantity, from_loc, to_loc, user_id):
        # Проверка за наличност при преместване
        current_stock = self.inventory_controller.get_stock_by_location(product_id, from_loc)
        if current_stock < float(quantity):
            raise ValueError(f"Няма достатъчно стока за преместване! Налично: {current_stock}")

        return self.add(product_id, user_id, None, "MOVE", quantity, "0",
                        from_location_id=from_loc, to_location_id=to_loc)

    def add(self, product_id: str, user_id: str, location_id: Optional[str], movement_type: str,
            quantity: str, price: Optional[str], customer: Optional[str] = None, supplier_id: Optional[str] = None,
            from_location_id: Optional[str] = None, to_location_id: Optional[str] = None) -> Movement:

        # Намиране на продукт
        full_product = self.product_controller.get_by_id(product_id)
        if not full_product:
            raise ValueError(f"Продукт с ID {product_id} не е намерен.")

        real_product_id = full_product.product_id
        historical_name = full_product.name
        historical_unit = full_product.unit

        # Намиране на потребител
        full_user = self.user_controller.get_by_id(user_id)
        if not full_user:
            raise ValueError(f"Потребител с ID {user_id} не е намерен.")
        user_id = full_user.user_id

        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        qty = MovementValidator.parse_quantity(quantity)

        # Доставчик
        final_supplier_id = None
        if m_type_str == "IN" and supplier_id:
            supplier = self.supplier_controller.get_by_id(supplier_id)
            final_supplier_id = supplier.supplier_id if supplier else str(supplier_id)

        # Цена
        if m_type_str == "MOVE":
            prc = 0.0
        else:
            if price is None or str(price).strip() == "":
                prc = float(full_product.price)
            else:
                prc = MovementValidator.parse_price(price)

        # Логика за локации
        if m_type_str == "MOVE":
            loc_from = self.location_controller.get_by_id(from_location_id)
            loc_to = self.location_controller.get_by_id(to_location_id)
            from_location_id = loc_from.location_id if loc_from else from_location_id
            to_location_id = loc_to.location_id if loc_to else to_location_id
        else:
            loc = self.location_controller.get_by_id(location_id)
            location_id = loc.location_id if loc else location_id

        # Физическо обновяване на инвентара
        if self.inventory_controller:
            if m_type_str == "IN":
                self.inventory_controller.increase_stock(real_product_id, qty, location_id)
            elif m_type_str == "OUT":
                # decrease_stock връща False, ако количеството е недостатъчно
                success = self.inventory_controller.decrease_stock(real_product_id, qty, location_id)
                if not success:
                    raise ValueError("Грешка при намаляване на наличността - недостатъчно количество.")
            elif m_type_str == "MOVE":
                self.inventory_controller.decrease_stock(real_product_id, qty, from_location_id)
                self.inventory_controller.increase_stock(real_product_id, qty, to_location_id)

        # Създаване на обект Movement
        movement = Movement(movement_id=None, product_id=real_product_id,
                            product_name=historical_name, user_id=user_id, location_id=location_id
            if m_type_str != "MOVE" else None, movement_type=MovementType[m_type_str],
                            quantity=qty, unit=historical_unit, price=prc,
                            supplier_id=final_supplier_id, customer=customer,
                            from_location_id=from_location_id, to_location_id=to_location_id)

        self.movements.append(movement)
        self.save_changes()

        # Логване и Фактуриране
        if self.activity_log_controller:
            self.activity_log_controller.log_action(user_id=user_id, action=f"MOVEMENT_{m_type_str}",
                                                    details=f"Продукт: {historical_name}, Кол: {qty}")

        if m_type_str == "OUT" and self.invoice_controller:
            self.invoice_controller.create_from_movement(movement=movement, product=full_product,
                                                         customer=customer or "Неизвестен клиент",
                                                         user_id=user_id)

        return movement

    def advanced_filter(self, movement_type=None, start_date=None, end_date=None,
                        product_id=None, location_id=None, user_id=None):
        results = []
        for m in self.movements:
            try:
                if isinstance(m.date, datetime):
                    m_date = m.date
                else:
                    m_date = datetime.strptime(str(m.date)[:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                continue

            if movement_type and m.movement_type.name != movement_type:
                continue
            if start_date and m_date.date() < start_date.date():
                continue
            if end_date and m_date.date() > end_date.date():
                continue
            if product_id and str(m.product_id) != str(product_id):
                continue
            if user_id and str(m.user_id) != str(user_id):
                continue
            if location_id:
                loc_id = str(location_id)
                if m.movement_type.name == "MOVE":
                    if m.from_location_id != loc_id and m.to_location_id != loc_id:
                        continue
                else:
                    if m.location_id != loc_id:
                        continue
            results.append(m)
        return results