from typing import Optional, List
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """Управлява наличностите в реално време."""
    def __init__(self, repository, product_controller, location_controller, movement_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller
        self.movement_controller = movement_controller
        self.data = self._load()
        self.update_inventory_from_movements(self.movement_controller.movements)



    def _load(self):
        data = self.repo.load()

        if not isinstance(data, dict):
            return {"products": {}}

        if "products" not in data or not isinstance(data["products"], dict):
            data["products"] = {}

        return data



    def _save(self):
        summary = self._build_inventory()
        self.repo.save(summary)



    def _product_id(self, user_input: str) -> Optional[str]:
        if not user_input:
            return None

        user_input = str(user_input).strip()

        if user_input in self.data.get("products", {}):
            return user_input

        for full_id in self.data.get("products", {}).keys():
            if full_id.startswith(user_input):
                return full_id

        for p in self.product_controller.get_all():
            if user_input.lower() == p.name.lower() or str(p.product_id).startswith(user_input):
                return str(p.product_id)

        return user_input




    def _location_id(self, user_input: str) -> Optional[str]:
        if not user_input:
            return None

        user_input = str(user_input).strip()

        loc = self.location_controller.get_by_id(user_input)
        if loc:
            return str(loc.location_id)

        for l in self.location_controller.get_all():
            if str(l.location_id).startswith(user_input):
                return str(l.location_id)

        return user_input

    def increase_stock(self, product_id: str, quantity: float, location_id: str):
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        qty = InventoryValidator.parse_and_validate_number(quantity, "Количество за заприходяване")

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locations = self.data["products"][pid]["locations"]
        current = float(locations.get(lid, 0.0))

        locations[lid] = round(current + qty, 3)



    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        qty = InventoryValidator.parse_and_validate_number(quantity, "Количество за изписване")

        current_stock = self.get_stock(pid, lid)


        product_obj = self.product_controller.get_by_id(pid)
        p_name = product_obj.name if product_obj else pid
        InventoryValidator.validate_stock_availability(qty, current_stock, p_name)

        locations = self.data["products"][pid]["locations"]
        locations[lid] = round(current_stock - qty, 3)
        return True



    def move_stock(self, product_id: str, quantity: float, from_location_id: str, to_location_id: str) -> bool:
        InventoryValidator.validate_move_locations(from_location_id, to_location_id)

        pid = self._product_id(product_id)
        qty = InventoryValidator.parse_and_validate_number(quantity, "Количество за трансфер")


        if self.decrease_stock(pid, qty, from_location_id):
            self.increase_stock(pid, qty, to_location_id)
            return True
        return False


    def get_total_stock(self, product_id: str) -> float:
        pid = self._product_id(product_id)

        products = self.data.get("products", {})
        product_info = products.get(pid, {})

        locations = product_info.get("locations", {})
        total = 0.0
        for qty in locations.values():
            try:
                total += float(qty)
            except:
                total += 0.0

        return total



    def get_stock(self, product_id, location_id):
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        products = self.data.get("products", {})

        if pid not in products:
            return 0.0

        product_info = products[pid]
        locations = product_info.get("locations", {})
        if lid not in locations:
            return 0.0

        try:
            return float(locations[lid])
        except:
            return 0.0




    def _build_inventory(self):
        rows = []

        for pid, p_info in self.data.get("products", {}).items():
            product_obj = self.product_controller.get_by_id(pid)
            if not product_obj:
                continue

            total = self.get_total_stock(pid)
            if total <= 0:
                continue

            warehouse_map = {}
            for lid, qty in p_info.get("locations", {}).items():
                if qty <= 0:
                    continue

                loc = self.location_controller.get_by_id(lid)
                name = loc.name if loc else "Неизвестен склад"
                warehouse_map[name] = qty

            movements = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            delivered = sum(float(m.quantity) for m in movements if m.movement_type.name == "IN")
            sold = sum(float(m.quantity) for m in movements if m.movement_type.name == "OUT")

            in_prices = [float(m.price) for m in movements if m.movement_type.name == "IN" and m.price]
            out_prices = [float(m.price) for m in movements if m.movement_type.name == "OUT" and m.price]

            avg_in = round(sum(in_prices) / len(in_prices), 2) if in_prices else 0.0
            avg_out = round(sum(out_prices) / len(out_prices), 2) if out_prices else 0.0

            expense = round(delivered * avg_in, 2)
            revenue = round(sold * avg_out, 2)


            if movements:
                last = sorted(movements, key=lambda x: x.date)[-1]
                last_movement = f"{last.movement_type.name} - {last.date}"
            else:
                last_movement = "Няма движения"

            rows.append({"product": product_obj.name, "unit": product_obj.unit, "total": total,
                         "warehouses": warehouse_map, "delivered": delivered, "sold": sold,
                         "avg_in_price": avg_in, "avg_out_price": avg_out, "expense": expense,
                         "revenue": revenue, "last_movement": last_movement})

        return {"products": rows, "summary": {"total_products": len(rows)}}





    def update_inventory_from_movements(self, movements):
        self.data = {"products": {}}

        for mv in movements:
            mtype = mv.movement_type.name
            if mtype == "MOVE":
                if mv.from_location_id is None or mv.to_location_id is None:
                    continue
                self.move_stock(mv.product_id, mv.quantity, mv.from_location_id, mv.to_location_id)
                continue

            if mv.location_id is None:
                continue

            if mtype == "IN":
                self.increase_stock(mv.product_id, mv.quantity, mv.location_id)
            elif mtype == "OUT":
                self.decrease_stock(mv.product_id, mv.quantity, mv.location_id)

        self._save()
