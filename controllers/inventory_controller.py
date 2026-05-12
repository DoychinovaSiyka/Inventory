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

    #   АВТОМАТИЧНО СЪЗДАВАНЕ НА ПРОДУКТ В ИНВЕНТАРА
    def _ensure_product(self, product_id: str):
        pid = str(product_id).strip()
        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

    #   нормализиране на short/long ID
    def _resolve_location_id(self, user_input: str) -> Optional[str]:
        """Приема short или long ID и връща long ID."""
        if not user_input:
            return None

        loc = self.location_controller.get_by_id(user_input)
        if not loc:
            return None

        return str(loc.location_id)

    def get_stock(self, product_id: str, location_id: str) -> float:
        pid = str(product_id or "").strip()
        lid = self._resolve_location_id(location_id)   # ← добавено

        #  продуктът дали съществува в инвентара
        if pid not in self.data.get("products", {}):
            return 0.0

        # Проверяваме дали локацията е валидна
        if not lid:
            return 0.0

        # Всички локации за този продукт
        product_info = self.data["products"][pid]
        locations = product_info.get("locations", {})

        # Количеството за конкретната локация
        raw_qty = locations.get(lid, 0.0)
        return InventoryValidator.parse_and_validate_number(raw_qty)

    def get_total_stock(self, product_id: str) -> float:
        """Връща общото количество от продукта във всички складове."""

        pid = str(product_id or "").strip()
        if pid not in self.data.get("products", {}):
            return 0.0

        product_info = self.data["products"][pid]
        locations = product_info.get("locations", {})
        total = 0.0

        for loc_id in locations:
            qty = locations[loc_id]
            qty = InventoryValidator.parse_and_validate_number(qty)
            total += qty

        return total

    def increase_stock(self, product_id: str, quantity: float, location_id: str) -> None:
        """Увеличава наличността по прост и разбираем начин."""

        pid = str(product_id or "").strip()
        lid = self._resolve_location_id(location_id)   # ← добавено

        if not lid:
            return

        qty_to_add = InventoryValidator.parse_and_validate_number(quantity, "Количество")

        # Ако продуктът не съществува - създаваме го
        if pid not in self.data.get("products", {}):
            self.data["products"][pid] = {"locations": {}}

        product_info = self.data["products"][pid]
        locations = product_info.get("locations", {})

        current_qty = locations.get(lid, 0.0)
        current_qty = InventoryValidator.parse_and_validate_number(current_qty)
        new_qty = current_qty + qty_to_add
        locations[lid] = round(new_qty, 2)

        self._save()

    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = str(product_id or "").strip()
        lid = self._resolve_location_id(location_id)   # ← добавено

        if pid not in self.data.get("products", {}):
            return False

        if not lid:
            return False

        qty_to_remove = InventoryValidator.parse_and_validate_number(quantity, "Количество")
        product_info = self.data["products"][pid]
        locations = product_info.get("locations", {})

        current_qty = locations.get(lid, 0.0)
        current_qty = InventoryValidator.parse_and_validate_number(current_qty)

        prod_obj = self.product_controller.get_by_id(pid)
        loc_obj = self.location_controller.get_by_id(lid)

        if prod_obj:
            product_name = prod_obj.name
        else:
            product_name = pid

        if loc_obj:
            location_name = loc_obj.name
        else:
            location_name = lid

        try:
            InventoryValidator.validate_stock_availability(product_name, qty_to_remove, current_qty, location_name)
        except ValueError:
            return False

        new_qty = current_qty - qty_to_remove
        locations[lid] = round(new_qty, 2)

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

            # нормализиране на ID-тата
            long_loc = self._resolve_location_id(m.location_id)
            long_from = self._resolve_location_id(m.from_location_id)
            long_to = self._resolve_location_id(m.to_location_id)

            if m_type == "IN" and long_loc:
                locs[long_loc] = round(locs.get(long_loc, 0.0) + qty, 2)

            elif m_type == "OUT" and long_loc:
                current = locs.get(long_loc, 0.0)
                locs[long_loc] = round(max(0.0, current - qty), 2)

            elif m_type == "MOVE":
                if long_from and long_to:
                    try:
                        InventoryValidator.validate_move_locations(long_from, long_to)

                        curr_from = locs.get(long_from, 0.0)
                        locs[long_from] = round(max(0.0, curr_from - qty), 2)

                        curr_to = locs.get(long_to, 0.0)
                        locs[long_to] = round(curr_to + qty, 2)
                    except ValueError:
                        continue

        self._save()
