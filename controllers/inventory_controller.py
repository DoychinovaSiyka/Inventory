from typing import Optional
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """Управлява наличностите в реално време и записва inventory.json като човешки отчет."""

    def __init__(self, repository, product_controller, location_controller, movement_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller
        self.movement_controller = movement_controller


        self.data = {"products": {}}
        self.rebuild_inventory_from_movements(self.movement_controller.movements)


    def _build_inventory(self):
        rows = []

        for p in self.product_controller.get_all():
            pid = str(p.product_id)

            total_stock = self.get_total_stock(pid)
            if total_stock == 0:
                continue

            # Складове с имена
            warehouse_map = {}
            inv_data = self.data.get("products", {}).get(pid, {})
            for loc_id, qty in inv_data.get("locations", {}).items():
                qty = float(qty)
                if qty > 0:
                    loc = self.location_controller.get_by_id(loc_id)
                    name = loc.name if loc else f"Склад {loc_id[:8]}"
                    warehouse_map[name] = qty

            # Движения за този продукт
            moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            delivered_qty = sum(float(m.quantity) for m in moves if m.movement_type.name == "IN")
            delivered_prices = [float(m.price) for m in moves if m.movement_type.name == "IN"]
            avg_in_price = round(sum(delivered_prices) / len(delivered_prices), 2) if delivered_prices else None

            sold_qty = sum(float(m.quantity) for m in moves if m.movement_type.name == "OUT")
            sold_prices = [float(m.price) for m in moves if m.movement_type.name == "OUT"]
            avg_out_price = round(sum(sold_prices) / len(sold_prices), 2) if sold_prices else None

            if moves:
                last_move = max(moves, key=lambda x: x.date)
                last_move_str = f"{last_move.movement_type.name} – {str(last_move.date)[:10]}"
            else:
                last_move_str = "–"

            row = {"product": p.name, "unit": p.unit, "total": total_stock, "warehouses": warehouse_map,
                   "delivered": delivered_qty, "sold": sold_qty, "avg_in_price": avg_in_price, "avg_out_price": avg_out_price,
                   "last_move": last_move_str}

            rows.append(row)

        return {"summary": {"total_products": len(rows)}, "products": rows}


    def _save(self) -> None:
        human = self._build_inventory()
        self.repo.save(human)

    def _ensure_product(self, product_id: str):
        pid = str(product_id).strip()
        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}



    def _resolve_product_id(self, user_input: str) -> Optional[str]:
        if not user_input:
            return None

        user_input = str(user_input).strip()

        if user_input in self.data.get("products", {}):
            return user_input

        for full_id in self.data.get("products", {}).keys():
            if full_id.startswith(user_input):
                return full_id

        return user_input


    def _resolve_location_id(self, user_input: str) -> Optional[str]:
        if not user_input:
            return None

        user_input = str(user_input).strip()

        loc = self.location_controller.get_by_id(user_input)
        if loc:
            return str(loc.location_id)

        for l in self.location_controller.get_all():
            if str(l.location_id).startswith(user_input):
                return str(l.location_id)

        return None


    def get_stock(self, product_id: str, location_id: str) -> float:
        pid = self._resolve_product_id(product_id)
        lid = self._resolve_location_id(location_id)

        if not pid or not lid:
            return 0.0

        product_info = self.data["products"].get(pid, {})
        locations = product_info.get("locations", {})

        raw_qty = locations.get(lid, 0.0)
        return InventoryValidator.parse_and_validate_number(raw_qty)

    def get_total_stock(self, product_id: str) -> float:
        pid = self._resolve_product_id(product_id)
        if not pid:
            return 0.0

        product_info = self.data["products"].get(pid, {})
        locations = product_info.get("locations", {})

        total = 0.0
        for _, qty in locations.items():
            total += InventoryValidator.parse_and_validate_number(qty)

        return total


    def increase_stock(self, product_id: str, quantity: float, location_id: str) -> None:
        pid = self._resolve_product_id(product_id)
        lid = self._resolve_location_id(location_id)

        if not pid or not lid:
            return

        qty_to_add = InventoryValidator.parse_and_validate_number(quantity, "Количество")

        self._ensure_product(pid)
        product_info = self.data["products"][pid]
        locations = product_info["locations"]

        current_qty = InventoryValidator.parse_and_validate_number(locations.get(lid, 0.0))
        locations[lid] = round(current_qty + qty_to_add, 2)



    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = self._resolve_product_id(product_id)
        lid = self._resolve_location_id(location_id)

        if not pid or not lid:
            return False

        self._ensure_product(pid)
        product_info = self.data["products"][pid]
        locations = product_info["locations"]

        qty_to_remove = InventoryValidator.parse_and_validate_number(quantity, "Количество")
        current_qty = InventoryValidator.parse_and_validate_number(locations.get(lid, 0.0))

        try:
            InventoryValidator.validate_stock_availability(product_info, qty_to_remove, current_qty, lid)
        except ValueError:
            return False

        locations[lid] = round(current_qty - qty_to_remove, 2)
        return True



    def move_stock(self, product_id: str, from_location_id: str, to_location_id: str, quantity: float) -> None:
        pid = self._resolve_product_id(product_id)
        from_lid = self._resolve_location_id(from_location_id)
        to_lid = self._resolve_location_id(to_location_id)

        if not pid or not from_lid or not to_lid:
            return

        self.decrease_stock(pid, quantity, from_lid)
        self.increase_stock(pid, quantity, to_lid)



    def rebuild_inventory_from_movements(self, movements) -> None:
        self.data = {"products": {}}

        for mv in movements:
            pid = str(mv.product_id)
            qty = mv.quantity
            mtype = mv.movement_type.name

            lid = mv.location_id
            from_lid = mv.from_location_id
            to_lid = mv.to_location_id

            if not pid:
                continue

            if mtype == "IN" and lid:
                self.increase_stock(pid, qty, lid)

            elif mtype == "OUT" and lid:
                self.decrease_stock(pid, qty, lid)

            elif mtype == "MOVE":
                if from_lid:
                    self.decrease_stock(pid, qty, from_lid)
                if to_lid:
                    self.increase_stock(pid, qty, to_lid)


        self._save()
