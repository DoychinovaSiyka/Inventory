from typing import Optional, List
from models.movement import Movement
from validators.inventory_validator import InventoryValidator
from controllers.abstract_controller import AbstractController
from controllers.product_controller import ProductController
from controllers.location_controller import LocationController
from controllers.movement_controller import MovementController


class InventoryController(AbstractController):
    def __init__(self, repo, product_controller, location_controller, movement_controller):
        super().__init__(repo)
        self.product_controller = product_controller
        self.location_controller = location_controller
        self.movement_controller = movement_controller

        self.data = []
        self.update_inventory_from_movements(self.movement_controller.movements)

    def from_dict(self, data):
        return data

    def to_dict(self, obj):
        return obj



    def _save(self):
        summary = self.build_inventory()
        self.save(summary)



    def _find_product(self, pid):
        for item in self.data:
            if item.get("product_id") == pid:
                return item
        return None





    def update_inventory_from_movements(self, movements: List[Movement]):
        self.data = []

        for mv in movements:
            pid = str(mv.product_id)
            qty = float(mv.quantity)
            mtype = mv.movement_type.name

            product = self._find_product(pid)
            if not product:
                product = {"product_id": pid, "warehouses": {}}
                self.data.append(product)

            warehouses = product["warehouses"]

            if mtype == "IN":
                lid = str(mv.location_id)
                warehouses[lid] = warehouses.get(lid, 0.0) + qty

            elif mtype == "OUT":
                lid = str(mv.location_id)
                warehouses[lid] = warehouses.get(lid, 0.0) - qty

            elif mtype == "MOVE":
                from_lid = str(mv.from_location_id)
                to_lid = str(mv.to_location_id)
                warehouses[from_lid] = warehouses.get(from_lid, 0.0) - qty
                warehouses[to_lid] = warehouses.get(to_lid, 0.0) + qty

        self._save()





    def get_total_stock(self, pid):
        product = self._find_product(pid)
        if not product:
            return 0.0
        return sum(float(q) for q in product.get("warehouses", {}).values())




    def get_stock(self, pid, lid):
        product = self._find_product(pid)
        if not product:
            return 0.0
        return float(product.get("warehouses", {}).get(lid, 0.0))





    def build_inventory(self):
        items = []

        for item in self.data:
            pid = item["product_id"]
            warehouses_raw = item["warehouses"]

            product = self.product_controller.get_by_id(pid)
            name = product.name if product else ""
            unit = product.unit if product else ""

            moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            total = self.get_total_stock(pid)

            warehouses = {}
            for lid, qty in warehouses_raw.items():
                loc = self.location_controller.get_by_id(lid)
                loc_name = loc.name if loc else f"Склад {lid}"
                warehouses[loc_name] = float(qty)

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

            if moves:
                last = max(moves, key=lambda m: m.date)
                last_movement = f"{last.movement_type.name} - {str(last.date)[:19]}"
            else:
                last_movement = "Няма движения"

            items.append({"product_id": pid, "product_name": name, "unit": unit, "total": total,
                          "warehouses": warehouses, "delivered": delivered, "sold": sold, "avg_in_price": avg_in,
                          "avg_out_price": avg_out, "expense": expense, "revenue": revenue,
                          "last_movement": last_movement})


        items.append({"total_products": len(items)})

        return items




    def get_critical_items(self, threshold=5):
        return [item for item in self.build_inventory() if "total_products" not in item and item["total"] <= threshold]



    def get_overstocked_items(self, threshold=130):
        return [item for item in self.build_inventory() if "total_products" not in item and item["total"] >= threshold]
