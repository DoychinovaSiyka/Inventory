from typing import Optional, List
from validators.inventory_validator import InventoryValidator
from controllers.abstract_controller import AbstractController
from controllers.product_controller import ProductController
from controllers.location_controller import LocationController
from controllers.movement_controller import MovementController





class InventoryController(AbstractController):
    def __init__(self, repo, product_controller: ProductController, location_controller: LocationController,
                 movement_controller: MovementController):

        super().__init__(repo)
        self.product_controller = product_controller
        self.location_controller = location_controller
        self.movement_controller = movement_controller

        raw_data = self.load()


        if isinstance(raw_data, dict):
            self.data = raw_data
        else:
            self.data = {}

        self.update_inventory_from_movements(self.movement_controller.movements)

    def from_dict(self, data):
        return data

    def to_dict(self, obj):
        return obj

    def _save(self):
        summary = self.build_inventory()
        self.save(summary)



    def _product_id(self, user_input: str) -> Optional[str]:
        """Намира продукт по пълно ID, частично ID или име и връща неговото ID."""
        if not user_input:
            return None

        user_input = str(user_input).strip()

        if user_input in self.data:
            return user_input

        for full_id in self.data.keys():
            if full_id.startswith(user_input):
                return full_id

        for p in self.product_controller.get_all():
            if user_input.lower() == p.name.lower() or str(p.product_id).startswith(user_input):
                return str(p.product_id)

        return user_input




    def _location_id(self, user_input: str) -> Optional[str]:
        """Намира локация по пълно или частично ID и връща нейното ID."""
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

        if pid not in self.data:
            self.data[pid] = {"warehouses": {}}

        warehouses = self.data[pid]["warehouses"]

        if lid not in warehouses:
            warehouses[lid] = 0.0

        current = float(warehouses.get(lid, 0.0))
        warehouses[lid] = round(current + qty, 3)




    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        qty = InventoryValidator.parse_and_validate_number(quantity, "Количество за изписване")

        current_stock = self.get_stock(pid, lid)

        product_obj = self.product_controller.get_by_id(pid)
        p_name = product_obj.name if product_obj else pid

        InventoryValidator.validate_stock_availability(qty, current_stock, p_name)

        warehouses = self.data[pid]["warehouses"]

        if lid not in warehouses:
            warehouses[lid] = 0.0
        warehouses[lid] = round(current_stock - qty, 3)
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

        product_info = self.data.get(pid, {})
        warehouses = product_info.get("warehouses", {})
        total = 0.0

        for qty in warehouses.values():
            try:
                total += float(qty)
            except:
                total += 0.0

        return total



    def get_stock(self, product_id, location_id):
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        if pid not in self.data:
            return 0.0

        warehouses = self.data[pid].get("warehouses", {})

        if lid not in warehouses:
            return 0.0

        try:
            return float(warehouses[lid])
        except:
            return 0.0



    def build_inventory(self):
        inventory = {}

        for pid, p_info in self.data.items():
            if pid == "summary":
                continue

            # Име и мерна единица
            product_obj = self.product_controller.get_by_id(pid)
            if product_obj:
                name = product_obj.name
                unit = product_obj.unit
            else:
                moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]
                if moves:
                    name = moves[0].product_name
                    unit = moves[0].unit
                else:
                    name = pid
                    unit = "бр."

            # Общо количество
            total = self.get_total_stock(pid)

            # Складове
            warehouses = {}
            for lid, qty in p_info.get("warehouses", {}).items():
                loc = self.location_controller.get_by_id(lid)
                loc_name = loc.name if loc else f"Склад {lid}"
                warehouses[loc_name] = float(qty)

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


            inventory[pid] = {"product_id": pid, "product_name": name, "unit": unit, "total": total,
                              "warehouses": warehouses, "delivered": delivered, "sold": sold,
                              "avg_in_price": avg_in, "avg_out_price": avg_out, "expense": expense, "revenue": revenue,
                              "last_movement": last_movement}

        return {**inventory, "summary": {"total_products": len(inventory)}}




    def update_inventory_from_movements(self, movements):
        self.data = {}
        sorted_movements = sorted(movements, key=lambda x: x.date)

        for mv in sorted_movements:
            mtype = mv.movement_type.name
            pid = str(mv.product_id)
            qty = float(mv.quantity)

            if pid not in self.data:
                self.data[pid] = {"warehouses": {}}

            warehouses = self.data[pid]["warehouses"]

            if mtype == "IN":
                lid = str(mv.location_id)
                current = warehouses.get(lid, 0.0)
                warehouses[lid] = round(current + qty, 3)

            elif mtype == "OUT":
                lid = str(mv.location_id)
                current = warehouses.get(lid, 0.0)
                warehouses[lid] = round(current - qty, 3)

            elif mtype == "MOVE":
                from_lid = str(mv.from_location_id)
                to_lid = str(mv.to_location_id)

                warehouses[from_lid] = round(warehouses.get(from_lid, 0.0) - qty, 3)
                warehouses[to_lid] = round(warehouses.get(to_lid, 0.0) + qty, 3)

        self._save()




    def get_critical_items(self, threshold=5):
        critical = []

        inventory = self.build_inventory()

        for pid, item in inventory.items():
            if pid == "summary":
                continue

            total = item.get("total", 0)

            if total <= threshold:
                critical.append({"product_id": pid, "product_name": item.get("product_name", "-"),
                                 "unit": item.get("unit", "-"), "total": total, "warehouses": item.get("warehouses", {})})

        return critical




    def get_overstocked_items(self, threshold=130):
        overstocked = []

        inventory = self.build_inventory()

        for pid, item in inventory.items():
            if pid == "summary":
                continue

            total = item.get("total", 0)

            if total >= threshold:
                overstocked.append({"product_id": pid, "product_name": item.get("product_name", "-"), "unit": item.get("unit", "-"),
                                    "total": total, "warehouses": item.get("warehouses", {})})

        return overstocked
