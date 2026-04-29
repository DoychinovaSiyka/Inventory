from typing import List
from storage.json_repository import JSONRepository


class InventoryController:
    def __init__(self, repository, product_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.data = self.repo.load() or {"products": {}}
        self.location_controller = None
        self.movement_controller = None

    def _save(self):
        self.repo.save(self.data)

    # --- ВИНАГИ СМЯТА ОБЩОТО ОТ locations ---
    def get_total_stock(self, product_id):
        product_id = str(product_id)
        if product_id not in self.data["products"]:
            return 0.0

        locations = self.data["products"][product_id].get("locations", {})
        return sum(float(qty) for qty in locations.values())

    # --- УВЕЛИЧАВАНЕ НА НАЛИЧНОСТ ---
    def increase_stock(self, product_id, quantity, location_id):
        product_id = str(product_id)
        quantity = float(quantity)

        if product_id not in self.data["products"]:
            self.data["products"][product_id] = {"locations": {}}

        prod_entry = self.data["products"][product_id]
        prod_entry["locations"][location_id] = prod_entry["locations"].get(location_id, 0) + quantity
        self._save()

    # --- НАМАЛЯВАНЕ НА НАЛИЧНОСТ ---
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

    # --- ПЪЛНО ПРЕСМЯТАНЕ ОТ ДВИЖЕНИЯ ---
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
                # OUT от from_location
                from_loc = m.from_location_id
                self.data["products"][pid]["locations"][from_loc] = \
                    self.data["products"][pid]["locations"].get(from_loc, 0) - qty

                # IN в to_location
                to_loc = m.to_location_id
                self.data["products"][pid]["locations"][to_loc] = \
                    self.data["products"][pid]["locations"].get(to_loc, 0) + qty

        self._save()

    # НАЧАЛНО ЗАРЕЖДАНЕ БЕЗ ДВИЖЕНИЯ
    def auto_seed_initial_stock(self, default_location_id):
        print(" Зареждам началните количества от products.json (без движения)...")

        for p in self.product_controller.get_all():
            qty = float(getattr(p, "quantity", 0))
            if qty <= 0:
                continue

            pid = p.product_id

            self.data["products"][pid] = {
                "locations": {default_location_id: qty}
            }

        self._save()
        print(" Началните количества са заредени в инвентара.")


    def calculate_fifo_cost(self, product_id, movements, fallback_price=0.0):
        product_id = str(product_id)
        batches = []
        total_cost = 0.0

        # сортираме движенията по дата (за всеки случай)
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
