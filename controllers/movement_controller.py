from datetime import datetime
from typing import Optional, List
from models.movement import Movement, MovementType
from validators.movement_validator import MovementValidator
from filters import movement_filters


class MovementController:
    """Управлява складовите движения и цените са исторически верни."""
    def __init__(self, repo, product_controller, user_controller, location_controller,
                 supplier_controller, invoice_controller, inventory_controller, activity_log_controller=None):

        self.repo = repo
        self.product_controller = product_controller
        self.user_controller = user_controller
        self.location_controller = location_controller
        self.supplier_controller = supplier_controller
        self.invoice_controller = invoice_controller
        self.inventory_controller = inventory_controller

        # Зареждане на движенията от базата
        raw = self.repo.load() or []
        self.movements: List[Movement] = []
        for m in raw:
            try:
                obj = Movement.from_dict(m)
                if obj:
                    self.movements.append(obj)
            except Exception:
                continue

    def get_all(self) -> List[Movement]:
        """Връща списък с всички движения."""
        return self.movements

    def save_changes(self) -> None:
        """Записва текущия списък с движения обратно в хранилището."""
        self.repo.save([m.to_dict() for m in self.movements])

    def add_in(self, product_id, quantity, price, location_id, supplier_id, user_id):
        """Доставка: Записва движение 'ВХОД' с конкретната доставна цена."""
        return self.add(product_id=product_id, user_id=user_id, location_id=location_id, movement_type="IN",
                        quantity=quantity, price=price, supplier_id=supplier_id)


    def add_out(self, product_id, quantity, customer, location_id, user_id, price):
        """Продажба: Записва движение 'ИЗХОД' с РЕАЛНАТА продажна цена."""
        # Проверка на наличността преди извършване на операцията
        current_stock = self.inventory_controller.get_stock(product_id, location_id)
        if current_stock < float(quantity):
            raise ValueError(f"Недостатъчна наличност в избрания склад! Налично: {current_stock}")

        return self.add(product_id=product_id, user_id=user_id, location_id=location_id,
                        movement_type="OUT", quantity=quantity, price=price, customer=customer)


    def move_stock(self, product_id, quantity, from_loc, to_loc, user_id):
        """Трансфер: Преместване на стока между два склада (без промяна на цена)."""
        return self.add(product_id=product_id, user_id=user_id, location_id=None,
                        movement_type="MOVE", quantity=quantity, price="0",
                        from_location_id=from_loc, to_location_id=to_loc)

    def add(self, product_id: str, user_id: str, location_id: Optional[str], movement_type: str,
            quantity: str, price: Optional[str], customer: Optional[str] = None, supplier_id: Optional[str] = None,
            from_location_id: Optional[str] = None, to_location_id: Optional[str] = None) -> Movement:
        """ Метод за създаване на движение. Синхронизация с инвентара и генериране на фактури."""




        product = self.product_controller.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не съществува в базата.")

        user = self.user_controller.get_by_id(user_id)
        if not user:
            raise ValueError("Потребителят не е намерен.")


        m_type_str = MovementValidator.normalize_movement_type(movement_type)
        qty = MovementValidator.parse_quantity(quantity)


        if m_type_str == "MOVE":
            prc = 0.0
        elif price is not None and str(price).strip() != "":
            prc = float(price)
        else:
            prc = float(product.price)

        # Синхронизиране на Инвентара
        if self.inventory_controller:
            if m_type_str == "IN":
                self.inventory_controller.increase_stock(product.product_id, qty, location_id)
            elif m_type_str == "OUT":
                self.inventory_controller.decrease_stock(product.product_id, qty, location_id)
            elif m_type_str == "MOVE":
                self.inventory_controller.decrease_stock(product.product_id, qty, from_location_id)
                self.inventory_controller.increase_stock(product.product_id, qty, to_location_id)


        movement = Movement(movement_id=None, product_id=product.product_id, product_name=product.name,
                            user_id=user.user_id, location_id=location_id, movement_type=MovementType[m_type_str],
                            quantity=qty, unit=product.unit, price=prc, supplier_id=supplier_id,
                            customer=customer or "Общ клиент", from_location_id=from_location_id,
                            to_location_id=to_location_id)


        self.movements.append(movement)
        self.save_changes()

        # Автоматично издаване на фактура при продажба
        if m_type_str == "OUT" and self.invoice_controller:
            try:
                self.invoice_controller.create_from_movement(movement=movement, product=product, customer=customer or "Общ клиент",
                                                             user_id=user.user_id)
            except Exception as e:
                print(f"Движението е записано, но фактурата не беше генерирана: {e}")

        return movement

    def advanced_filter(self, **kwargs) -> List[Movement]:
        """Филтриране на историята по различни критерии."""
        return movement_filters.filter_advanced(self.movements, **kwargs)

    def filter_deliveries(self, keyword: str) -> List[Movement]:
        """филтриране само за доставки (IN)."""
        return movement_filters.filter_deliveries(self.movements, keyword, self.product_controller, self.supplier_controller)