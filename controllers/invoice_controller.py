from typing import List
from storage.json_repository import JSONRepository


class InventoryController:
    def __init__(self, repository, product_controller, movement_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.data = self.repo.load() or {"products": {}}

    def _save(self):
        self.repo.save(self.data)

    # СМЯТА ОБЩОТО ОТ locations
    def get_total_stock(self, product_id):
        product_id = str(product_id)
        if product_id not in self.data["products"]:
            return 0.0

        locations = self.data["products"][product_id].get("locations", {})
        return sum(float(qty) for qty in locations.values())

    def increase_stock(self, product_id, quantity, location_id):
        product_id = str(product_id)
        quantity = float(quantity)

        if product_id not in self.data["products"]:
            self.data["products"][product_id] = {"locations": {}}

        prod_entry = self.data["products"][product_id]
        prod_entry["locations"][location_id] = prod_entry["locations"].get(location_id, 0) + quantity
        self._save()

    def decrease_stock(self, product_id, quantity, location_id):
        product_id = str(product_id)
        quantity = float(quantity)

        if self.get_total_stock(product_id) < quantity:
            return False

        if product_id not in self.data["products"]:
            self.data["products"][product_id] = {"locations": {}}

        prod_entry = self.data["products"][product_id]
        prod_entry["locations"][location_id] = prod_entry["locations"].get(location_id, 0) - quantity
        self._save()
        return True

    # ПЪЛНО ПРЕСМЯТАНЕ ОТ ДВИЖЕНИЯ
    def rebuild_inventory_from_movements(self, movements):
        self.data = {"products": {}}

        for m in movements:
            pid = m.product_id
            qty = float(m.quantity)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            m_type = m.movement_type.name
            if m_type == "IN":
                loc = m.location_id
                self.data["products"][pid]["locations"][loc] = \
                    self.data["products"][pid]["locations"].get(loc, 0) + qty

            elif m_type == "OUT":
                loc = m.location_id
                self.data["products"][pid]["locations"][loc] = \
                    self.data["products"][pid]["locations"].get(loc, 0) - qty

            elif m_type == "MOVE":
                from_loc = m.from_location_id
                to_loc = m.to_location_id

                self.data["products"][pid]["locations"][from_loc] = \
                    self.data["products"][pid]["locations"].get(from_loc, 0) - qty

                self.data["products"][pid]["locations"][to_loc] = \
                    self.data["products"][pid]["locations"].get(to_loc, 0) + qty

        self._save()

    def calculate_fifo_cost(self, product_id, movements, fallback_price=0.0):
        product_id = str(product_id)
        batches = []
        total_cost = 0.0

        relevant = [m for m in movements if str(m.product_id) == product_id]
        relevant.sort(key=lambda x: x.date)

        for m in relevant:
            mtype = m.movement_type.name
            qty = float(m.quantity)

            if mtype == "IN":
                price = float(m.price if m.price is not None else fallback_price)
                batches.append({"qty": qty, "price": price})

            elif mtype == "OUT":
                need = qty
                while need > 0 and batches:
                    b = batches[0]
                    if b["qty"] <= need:
                        total_cost += b["qty"] * b["price"]
                        need -= b["qty"]
                        batches.pop(0)
                    else:
                        total_cost += need * b["price"]
                        b["qty"] -= need
                        need = 0

        return total_cost

    def get_warehouses_with_product(self, product_name):
        result = []
        for product_id, pdata in self.data.get("products", {}).items():
            product = self.product_controller.get_by_id(product_id)
            if not product:
                continue

            if product.name.lower() == product_name.lower():
                locations = pdata.get("locations", {})
                for warehouse_id, qty in locations.items():
                    if qty > 0:
                        result.append((warehouse_id, qty))
                return result

        return []

    def get_total_inventory_value_fifo(self, movement_controller):
        total_value = 0.0

        for pid, pdata in self.data.get("products", {}).items():
            product = self.product_controller.get_by_id(pid)
            if not product:
                continue

            current_stock = self.get_total_stock(pid)
            if current_stock <= 0:
                continue

            total_purchase_expense = 0.0
            total_in_qty = 0.0

            for m in movement_controller.movements:
                if str(m.product_id) == str(pid) and m.movement_type.name == "IN":
                    qty = float(m.quantity or 0)
                    price = float(m.price if m.price is not None else product.price)
                    total_purchase_expense += qty * price
                    total_in_qty += qty

            if total_in_qty > 0:
                avg_price = total_purchase_expense / total_in_qty
                total_value += current_stock * avg_price
            else:
                total_value += current_stock * float(product.price or 0)

        return total_value
