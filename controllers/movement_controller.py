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

    # ---------------------------------------------------------
    # Зареждане на движенията от JSON
    # ---------------------------------------------------------
    def _load_movements(self) -> List[Movement]:
        raw = self.repo.load() or []
        return [Movement.from_dict(m) for m in raw]

    # ---------------------------------------------------------
    # Записване на движенията
    # ---------------------------------------------------------
    def save_changes(self) -> None:
        self.repo.save([m.to_dict() for m in self.movements])

    # ---------------------------------------------------------
    # Търсене по описание (за меню опция 3)
    # ---------------------------------------------------------
    def search_by_description(self, keyword: str) -> List[Movement]:
        keyword = keyword.lower()
        results = []

        for m in self.movements:
            # --- СЪБИРАМЕ ДАННИТЕ ОТ ВСИЧКИ КОЛОНИ ---

            # 1. Дата (ако потребителят търси по "2026-04-29")
            m_date = str(m.date).lower()

            # 2. Продукт
            m_product = (m.product_name or "").lower()

            # 3. Тип (IN, OUT, MOVE)
            m_type = m.movement_type.name.lower()

            # 4. Към/От (Партньор - Доставчик или Клиент)
            partner = ""
            if m.movement_type.name == "IN" and m.supplier_id:
                supp = self.supplier_controller.get_by_id(m.supplier_id) if self.supplier_controller else None
                partner = (supp.name.lower() if supp else m.supplier_id.lower())
            elif m.movement_type.name == "OUT":
                partner = (m.customer or "").lower()

            # 5. Склад (Локация)
            location_info = ""
            if m.movement_type.name == "MOVE":
                loc_from = self.location_controller.get_by_id(m.from_location_id)
                loc_to = self.location_controller.get_by_id(m.to_location_id)
                location_info = f"{(loc_from.name if loc_from else '').lower()} {(loc_to.name if loc_to else '').lower()}"
            else:
                loc_obj = self.location_controller.get_by_id(m.location_id)
                location_info = (loc_obj.name or "").lower() if loc_obj else (m.location_id or "").lower()

            # --- ПРОВЕРКА: Има ли съвпадение в някоя от колоните? ---
            if (keyword in m_date or
                    keyword in m_product or
                    keyword in m_type or
                    keyword in partner or
                    keyword in location_info or
                    keyword in (m.description or "").lower()):
                results.append(m)

        return results

    # ---------------------------------------------------------
    # Добавяне на движение (IN / OUT / MOVE)
    # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # ОБНОВЯВАНЕ НА ИНВЕНТАРА
        # ---------------------------------------------------------
        if self.inventory_controller:
            if m_type_str == "IN":
                self.inventory_controller.increase_stock(product_id, qty, location_id)

            elif m_type_str == "OUT":
                self.inventory_controller.decrease_stock(product_id, qty, location_id)

            elif m_type_str == "MOVE":
                self.inventory_controller.decrease_stock(product_id, qty, from_location_id)
                self.inventory_controller.increase_stock(product_id, qty, to_location_id)

        # ---------------------------------------------------------
        # СЪЗДАВАНЕ НА ДВИЖЕНИЕ
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # СЪЗДАВАНЕ НА ФАКТУРА ПРИ OUT
        # ---------------------------------------------------------
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

        results = []

        for m in self.movements:
            # --- Тип ---
            if movement_type and m.movement_type.name != movement_type:
                continue

            # --- Начална дата ---
            if start_date and m.date < start_date:
                continue

            # --- Крайна дата ---
            if end_date and m.date > end_date:
                continue

            # --- Продукт ---
            if product_id and str(m.product_id) != str(product_id):
                continue

            # --- Локация ---
            if location_id:
                if m.movement_type == MovementType.MOVE:
                    if m.from_location_id != location_id and m.to_location_id != location_id:
                        continue
                else:
                    if m.location_id != location_id:
                        continue

            # --- Потребител ---
            if user_id and str(m.user_id) != str(user_id):
                continue

            results.append(m)

        return results

