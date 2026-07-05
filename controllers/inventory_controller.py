from typing import Optional, List
from validators.inventory_validator import InventoryValidator
from controllers.abstract_controller import AbstractController





class InventoryController(AbstractController):
    def __init__(self, repository, product_controller, location_controller, movement_controller):
        super().__init__(repository)

        self.product_controller = product_controller
        self.location_controller = location_controller
        self.movement_controller = movement_controller

        raw_data = self.load()
        if isinstance(raw_data, dict) and "products" in raw_data and isinstance(raw_data["products"], dict):
            self.data = raw_data
        else:
            self.data = {"products": {}}

        # Пресмятаме инвентара на база движенията
        self.update_inventory_from_movements(self.movement_controller.movements)


    def from_dict(self, data):
        return data

    def to_dict(self, obj):
        return obj

    def _save(self):
        summary = self.build_inventory()
        self.save(summary)


    # Намираме ID на продукт
    def _product_id(self, user_input: str) -> Optional[str]:
        if not user_input:
            return None

        user_input = str(user_input).strip()

        # директно ID
        if user_input in self.data.get("products", {}):
            return user_input

        # частично ID
        for full_id in self.data.get("products", {}).keys():
            if full_id.startswith(user_input):
                return full_id

        # по име
        for p in self.product_controller.get_all():
            if user_input.lower() == p.name.lower() or str(p.product_id).startswith(user_input):
                return str(p.product_id)

        return user_input


    # Намираме ID на склад
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


    # Увеличаваме наличността
    def increase_stock(self, product_id: str, quantity: float, location_id: str):
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        qty = InventoryValidator.parse_and_validate_number(quantity, "Количество за заприходяване")

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locations = self.data["products"][pid]["locations"]
        current = float(locations.get(lid, 0.0))

        locations[lid] = round(current + qty, 3)


    # Намаляваме наличността
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


    # Преместване между складове
    def move_stock(self, product_id: str, quantity: float, from_location_id: str, to_location_id: str) -> bool:
        InventoryValidator.validate_move_locations(from_location_id, to_location_id)

        pid = self._product_id(product_id)
        qty = InventoryValidator.parse_and_validate_number(quantity, "Количество за трансфер")

        if self.decrease_stock(pid, qty, from_location_id):
            self.increase_stock(pid, qty, to_location_id)
            return True
        return False


    # Общо количество от продукт
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


    # Количество в конкретен склад
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

    def build_inventory(self):
        products_dict = {}

        for pid, p_info in self.data.get("products", {}).items():
            product_obj = self.product_controller.get_by_id(pid)
            if product_obj:
                product_name = product_obj.name
                unit = product_obj.unit
            else:
                moves_for_product = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

                if moves_for_product:
                    product_name = moves_for_product[0].product_name
                    unit = moves_for_product[0].unit
                else:
                    product_name = pid
                    unit = "бр."

            # Общо количество
            total = self.get_total_stock(pid)

            # Разпределение по складове
            warehouse_map = {}
            for lid, qty in p_info.get("locations", {}).items():
                loc = self.location_controller.get_by_id(lid)
                name = loc.name if loc else f"Склад {lid}"
                warehouse_map[name] = float(qty)

            # Движения
            moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            in_moves = [m for m in moves if m.movement_type.name == "IN"]
            out_moves = [m for m in moves if m.movement_type.name == "OUT"]

            delivered = sum(float(m.quantity) for m in in_moves)
            sold = sum(float(m.quantity) for m in out_moves)

            in_prices = [float(m.price) for m in in_moves if m.price]
            out_prices = [float(m.price) for m in out_moves if m.price]

            avg_in = round(sum(in_prices) / len(in_prices), 2) if in_prices else 0.0
            avg_out = round(sum(out_prices) / len(out_prices), 2) if out_prices else 0.0

            expense = round(delivered * avg_in, 2)
            revenue = round(sold * avg_out, 2)

            # Последно движение
            if moves:
                last = sorted(moves, key=lambda x: x.date)[-1]
                last_movement = f"{last.movement_type.name} - {str(last.date)[:19]}"
            else:
                last_movement = "Няма движения"


            products_dict[pid] = {"product_id": pid, "product_name": product_name,
                                  "unit": unit, "total": total, "warehouses": warehouse_map,
                                  "delivered": delivered, "sold": sold, "avg_in_price": avg_in,
                                  "avg_out_price": avg_out, "expense": expense, "revenue": revenue,
                                  "last_movement": last_movement}

        return {"products": products_dict, "summary": {"total_products": len(products_dict)}}





    # Пресмятаме инвентара от движенията
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

                locations[from_lid] = round(locations.get(from_lid, 0.0) - qty, 3)
                locations[to_lid] = round(locations.get(to_lid, 0.0) + qty, 3)

        self._save()

    def get_critical_items(self, threshold=5):
        """Връща списък с критично изчерпани артикули."""
        critical = []

        inventory = self.build_inventory()["products"]

        for pid, item in inventory.items():
            total = item.get("total", 0)

            if total <= threshold:
                critical.append({
                    "product_id": pid,
                    "product_name": item.get("product_name", "-"),
                    "unit": item.get("unit", "-"),
                    "total": total,
                    "warehouses": item.get("warehouses", {})
                })

        return critical
