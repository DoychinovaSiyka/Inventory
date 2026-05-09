from datetime import datetime
from typing import Optional, List
from models.movement import Movement, MovementType
from validators.movement_validator import MovementValidator
from filters import movement_filters


class MovementController:
    def __init__(self, repo, product_controller, user_controller, location_controller,
                 supplier_controller, invoice_controller, inventory_controller, activity_log_controller=None):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.invoice_controller = invoice_controller
        self.inventory_controller = inventory_controller

        raw = self.repo.load() or []
        self.movements: List[Movement] = []
        for m in raw:
            obj = Movement.from_dict(m)
            if obj:
                self.movements.append(obj)

    def get_all(self) -> List[Movement]:
        return self.movements

    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    def add_in(self, product_id, quantity, price, location_id, supplier_id, user_id):
        return self.add(product_id=product_id, user_id=user_id, location_id=location_id,
                        movement_type="IN", quantity=quantity, price=price, supplier_id=supplier_id)

    def add_out(self, product_id, quantity, customer, location_id, user_id):
        current_stock = self.inventory_controller.get_stock_by_location(product_id, location_id)
        if current_stock < float(quantity):
            raise ValueError(f"Недостатъчна наличност! Налично: {current_stock}, Искано: {quantity}")

        return self.add(product_id=product_id, user_id=user_id, location_id=location_id,
                        movement_type="OUT", quantity=quantity, price=None, customer=customer)

    def move_stock(self, product_id, quantity, from_loc, to_loc, user_id):
        current_stock = self.inventory_controller.get_stock_by_location(product_id, from_loc)
        if current_stock < float(quantity):
            raise ValueError(f"Няма достатъчно стока! Налично: {current_stock}")

        return self.add(product_id=product_id, user_id=user_id, location_id=None,
                        movement_type="MOVE", quantity=quantity, price="0",
                        from_location_id=from_loc, to_location_id=to_loc)

    def add(self, product_id: str, user_id: str, location_id: Optional[str], movement_type: str,
            quantity: str, price: Optional[str], customer: Optional[str] = None, supplier_id: Optional[str] = None,
            from_location_id: Optional[str] = None, to_location_id: Optional[str] = None) -> Movement:

        full_product = self.product_controller.get_by_id(product_id)
        if not full_product:
            raise ValueError(f"Продукт {product_id} не е намерен.")

        real_product_id = full_product.product_id
        historical_name = full_product.name
        historical_unit = full_product.unit

        full_user = self.user_controller.get_by_id(user_id)
        if not full_user:
            raise ValueError(f"Потребител {user_id} не е намерен.")

        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        qty = MovementValidator.parse_quantity(quantity)

        # Логика за доставчик
        final_supplier_id = None
        if m_type_str == "IN" and supplier_id:
            supplier = self.supplier_controller.get_by_id(supplier_id)
            final_supplier_id = supplier.supplier_id if supplier else str(supplier_id)

        # Логика за цена
        prc = 0.0 if m_type_str == "MOVE" else (
            MovementValidator.parse_price(price) if price else float(full_product.price))

        # Логика за локации
        if m_type_str == "MOVE":
            loc_from = self.location_controller.get_by_id(from_location_id)
            from_location_id = loc_from.location_id if loc_from else from_location_id
            loc_to = self.location_controller.get_by_id(to_location_id)
            to_location_id = loc_to.location_id if loc_to else to_location_id
            movement_location_id = None
        else:
            loc = self.location_controller.get_by_id(location_id)
            movement_location_id = loc.location_id if loc else location_id

        # Обновяване на инвентара
        if self.inventory_controller:
            if m_type_str == "IN":
                self.inventory_controller.increase_stock(real_product_id, qty, movement_location_id)
            elif m_type_str == "OUT":
                self.inventory_controller.decrease_stock(real_product_id, qty, movement_location_id)
            elif m_type_str == "MOVE":
                self.inventory_controller.decrease_stock(real_product_id, qty, from_location_id)
                self.inventory_controller.increase_stock(real_product_id, qty, to_location_id)

        movement = Movement(movement_id=None, product_id=real_product_id, product_name=historical_name,
                            user_id=full_user.user_id, location_id=movement_location_id,
                            movement_type=MovementType[m_type_str], quantity=qty, unit=historical_unit,
                            price=prc, supplier_id=final_supplier_id, customer=customer or "Общ клиент",
                            from_location_id=from_location_id, to_location_id=to_location_id)

        self.movements.append(movement)
        self.save_changes()

        # Фактура при OUT
        if m_type_str == "OUT" and self.invoice_controller:
            self.invoice_controller.create_from_movement(movement=movement, product=full_product,
                                                         customer=customer or "Общ клиент", user_id=full_user.user_id)
        return movement



    def advanced_filter(self, **kwargs) -> List[Movement]:
        """Филтър за разширено търсене."""
        return movement_filters.filter_advanced(self.movements, **kwargs)

    def filter_deliveries(self, keyword: str) -> List[Movement]:
        """Филтър специално за доставки."""
        return movement_filters.filter_deliveries(self.movements, keyword, self.product_controller, self.supplier_controller)