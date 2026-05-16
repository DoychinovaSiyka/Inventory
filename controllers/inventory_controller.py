from typing import Optional, List
from validators.inventory_validator import InventoryValidator




class InventoryController:
    """Управлява наличностите в реално време - колко стока има и в кой склад се намира."""
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
        """Данните за наличност, необходими за базата данни."""
        rows = []

        for pid, p_info in self.data.get("products", {}).items():
            product_obj = self.product_controller.get_by_id(pid)
            if not product_obj:
                continue

            total = self.get_total_stock(pid)

            warehouse_map = {}
            for lid, qty in p_info.get("locations", {}).items():
                loc = self.location_controller.get_by_id(lid)
                name = loc.name if loc else f"Склад {lid}"
                warehouse_map[name] = float(qty)


            rows.append({"product_id": pid, "product_name": product_obj.name, "unit": product_obj.unit,
                         "total": total, "warehouses": warehouse_map})

        return {"products": rows, "summary": {"total_products": len(rows)}}



    def update_inventory_from_movements(self, movements):
        self.data = {"products": {}}

        sorted_movements = sorted(movements, key=lambda x: x.date)
        for mv in sorted_movements:
            mtype = mv.movement_type.name
            pid = str(mv.product_id)
            qty = float(mv.quantity)


            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locations = self.data["products"][pid]["locations"]

            if mtype == "IN":
                lid = str(mv.location_id)
                current = locations.get(lid, 0.0)
                locations[lid] = round(current + qty, 3)

            elif mtype == "OUT":
                lid = str(mv.location_id)
                current = locations.get(lid, 0.0)
                locations[lid] = round(current - qty, 3)

            elif mtype == "MOVE":
                from_lid = str(mv.from_location_id)
                to_lid = str(mv.to_location_id)

                # Вадим от стария склад
                locations[from_lid] = round(locations.get(from_lid, 0.0) - qty, 3)
                # Добавяме в новия
                locations[to_lid] = round(locations.get(to_lid, 0.0) + qty, 3)

        self._save()