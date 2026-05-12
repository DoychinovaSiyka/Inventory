from typing import List, Dict, Optional
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """Управлява наличностите в реално време и поддържа финансови изчисления."""

    def __init__(self, repository, product_controller, location_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller

        raw = self.repo.load()
        self.data = raw if (raw and "products" in raw) else {"products": {}}

    def _save(self) -> None:
        """Записва текущото състояние в хранилището."""
        self.repo.save(self.data)

    def _resolve_ids(self, product_id: str, location_id: Optional[str] = None):
        """Превръща частични ID-та в пълни системни UUID-та."""
        prod = self.product_controller.get_by_id(str(product_id))
        full_pid = prod.product_id if prod else str(product_id)

        full_lid = None
        if location_id:
            loc = self.location_controller.get_by_id(str(location_id))
            full_lid = loc.location_id if loc else str(location_id)

        return full_pid, full_lid

    def get_stock(self, product_id: str, location_id: str) -> float:
        """Връща наличността на продукт в конкретен склад."""
        pid, lid = self._resolve_ids(product_id, location_id)
        if not lid or pid not in self.data["products"]:
            return 0.0

        locs = self.data["products"][pid].get("locations", {})
        return InventoryValidator.parse_and_validate_number(locs.get(lid, 0.0))


    def get_total_stock(self, product_id: str) -> float:
        """Общо количество от продукта във всички складове."""
        pid, _ = self._resolve_ids(product_id)
        if pid not in self.data["products"]:
            return 0.0

        locs = self.data["products"][pid].get("locations", {})
        return sum(InventoryValidator.parse_and_validate_number(q) for q in locs.values())

    def increase_stock(self, product_id: str, quantity: float, location_id: str) -> None:
        """Увеличава наличността с валидация на количеството."""
        pid, lid = self._resolve_ids(product_id, location_id)
        if not lid:
            return

        valid_qty = InventoryValidator.parse_and_validate_number(quantity, "Количество")

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locs = self.data["products"][pid]["locations"]
        current = InventoryValidator.parse_and_validate_number(locs.get(lid, 0.0))

        locs[lid] = round(current + valid_qty, 2)
        self._save()

    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        """Намалява наличност, използвайки бизнес логиката на Валидатора."""
        pid, lid = self._resolve_ids(product_id, location_id)

        if not lid or pid not in self.data["products"]:
            return False

        qty_to_remove = InventoryValidator.parse_and_validate_number(quantity, "Количество")
        locs = self.data["products"][pid]["locations"]
        current = InventoryValidator.parse_and_validate_number(locs.get(lid, 0.0))

        try:
            prod_obj = self.product_controller.get_by_id(pid)
            loc_obj = self.location_controller.get_by_id(lid)
            p_name = prod_obj.name if prod_obj else pid
            l_name = loc_obj.name if loc_obj else lid

            InventoryValidator.validate_stock_availability(p_name, qty_to_remove, current, l_name)
        except ValueError:
            return False  # Недостатъчна наличност

        locs[lid] = round(current - qty_to_remove, 2)
        self._save()
        return True

    def rebuild_inventory_from_movements(self, movements: List) -> None:
        """Преизчислява целия инвентар от историята."""
        self.data = {"products": {}}

        sorted_moves = sorted(movements, key=lambda m: m.date)
        for m in sorted_moves:
            pid = str(m.product_id)
            qty = InventoryValidator.parse_and_validate_number(m.quantity)

            try:
                m_type = m.movement_type.name
            except Exception:
                m_type = str(m.movement_type)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locs = self.data["products"][pid]["locations"]

            if m_type == "IN" and m.location_id:
                locs[m.location_id] = round(locs.get(m.location_id, 0.0) + qty, 2)

            elif m_type == "OUT" and m.location_id:
                current = locs.get(m.location_id, 0.0)
                locs[m.location_id] = round(max(0.0, current - qty), 2)

            elif m_type == "MOVE":
                # Добавяме проверка за еднакви складове при преместване
                if m.from_location_id and m.to_location_id:
                    try:
                        InventoryValidator.validate_move_locations(m.from_location_id, m.to_location_id)

                        # Намаляваме от източника
                        curr_from = locs.get(m.from_location_id, 0.0)
                        locs[m.from_location_id] = round(max(0.0, curr_from - qty), 2)

                        # Увеличаваме в целта
                        curr_to = locs.get(m.to_location_id, 0.0)
                        locs[m.to_location_id] = round(curr_to + qty, 2)
                    except ValueError:
                        continue  # Прескачаме некоректни премествания

        self._save()

    def sort_products_by_quantity(self, reverse=True):
        """Връща продуктите, сортирани по общо количество."""
        products = self.product_controller.get_all()
        return sorted(products, key=lambda p: self.get_total_stock(p.product_id), reverse=reverse)

    def calculate_fifo_cost(self, product_id: str, movements: List, fallback_price: float = 0.0) -> float:
        """Пресмята себестойност по FIFO."""
        pid, _ = self._resolve_ids(product_id)

        total_sold = 0.0
        for m in movements:
            m_type = getattr(m.movement_type, 'name', str(m.movement_type))
            if str(m.product_id) == pid and m_type == "OUT":
                total_sold += InventoryValidator.parse_and_validate_number(m.quantity)

        if total_sold <= 0:
            return 0.0

        batches = []
        for m in sorted(movements, key=lambda x: x.date):
            m_type = getattr(m.movement_type, 'name', str(m.movement_type))
            if str(m.product_id) == pid and m_type == "IN":
                price = InventoryValidator.parse_and_validate_number(m.price) if m.price else fallback_price
                qty = InventoryValidator.parse_and_validate_number(m.quantity)
                batches.append({"qty": qty, "price": price})

        total_cost = 0.0
        remaining = total_sold
        for batch in batches:
            if remaining <= 0: break
            take = min(batch["qty"], remaining)
            total_cost += take * batch["price"]
            remaining -= take

        if remaining > 0:
            total_cost += remaining * fallback_price

        return round(total_cost, 2)

    def get_total_inventory_value_fifo(self, movement_controller) -> float:
        """Пълна финансова стойност на склада."""
        total_value = 0.0
        all_moves = movement_controller.get_all()

        for pid in self.data.get("products", {}):
            product_obj = self.product_controller.get_by_id(pid)
            fb_price = float(product_obj.price) if product_obj else 0.0

            prod_moves = sorted([m for m in all_moves if str(m.product_id) == pid], key=lambda x: x.date)
            batches = []

            for m in prod_moves:
                m_type = getattr(m.movement_type, 'name', str(m.movement_type))
                qty = InventoryValidator.parse_and_validate_number(m.quantity)

                if m_type == "IN":
                    price = InventoryValidator.parse_and_validate_number(m.price) if m.price else fb_price
                    batches.append({"qty": qty, "price": price})
                elif m_type == "OUT":
                    while qty > 0 and batches:
                        if batches[0]["qty"] <= qty:
                            qty -= batches[0]["qty"]
                            batches.pop(0)
                        else:
                            batches[0]["qty"] -= qty
                            qty = 0

            for b in batches:
                total_value += b["qty"] * b["price"]

        return round(total_value, 2)