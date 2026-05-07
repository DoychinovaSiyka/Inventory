from typing import List, Dict


class InventoryController:
    def __init__(self, repository, product_controller, location_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller

        raw = self.repo.load()
        if raw:
            self.data = raw
        else:
            self.data = {"products": {}}

    def _save(self):
        self.repo.save(self.data)


    def _get_full_product_id(self, input_id: str) -> str:
        product = self.product_controller.get_by_id(str(input_id))
        if product:
            return product.product_id
        return str(input_id)

    def _get_full_location_id(self, input_id: str) -> str:
        if not input_id:
            return None

        loc = self.location_controller.get_by_id(str(input_id))
        if loc:
            return loc.location_id

        # ако складът не съществува - НЕ връщаме произволен ID
        return None


    # Основни справки
    def get_stock_by_location(self, product_id: str, location_id: str) -> float:
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid:
            return 0.0

        if pid not in self.data["products"]:
            return 0.0

        locations = self.data["products"][pid].get("locations", {})
        return float(locations.get(lid, 0.0))

    def get_total_stock(self, product_id: str) -> float:
        pid = self._get_full_product_id(product_id)

        if pid not in self.data["products"]:
            return 0.0

        locations = self.data["products"][pid].get("locations", {})
        total = 0.0

        for qty in locations.values():
            total += float(qty)

        return total


    def increase_stock(self, product_id: str, quantity: float, location_id: str):
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid:
            return

        qty_to_add = float(quantity)

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locations = self.data["products"][pid]["locations"]

        current = float(locations.get(lid, 0.0))
        locations[lid] = current + qty_to_add

        self._save()

    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid:
            return False

        qty_to_remove = float(quantity)

        if pid not in self.data["products"]:
            return False

        locations = self.data["products"][pid]["locations"]
        current = float(locations.get(lid, 0.0))

        if current < qty_to_remove:
            return False

        locations[lid] = current - qty_to_remove
        self._save()
        return True



    def rebuild_inventory_from_movements(self, movements: List):
        self.data = {"products": {}}

        sorted_movements = sorted(movements, key=lambda x: x.date)

        for m in sorted_movements:
            pid = str(m.product_id)
            qty = float(m.quantity)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locations = self.data["products"][pid]["locations"]
            m_type = m.movement_type.name

            # IN
            if m_type == "IN":
                if m.location_id:
                    lid = str(m.location_id)
                    current = float(locations.get(lid, 0.0))
                    locations[lid] = current + qty

            # OUT
            elif m_type == "OUT":
                if m.location_id:
                    lid = str(m.location_id)
                    current = float(locations.get(lid, 0.0))
                    new_val = current - qty
                    if new_val < 0:
                        new_val = 0.0
                    locations[lid] = new_val

            # MOVE
            elif m_type == "MOVE":
                from_loc = m.from_location_id
                to_loc = m.to_location_id

                if from_loc:
                    from_loc = str(from_loc)
                    current = float(locations.get(from_loc, 0.0))
                    new_val = current - qty
                    if new_val < 0:
                        new_val = 0.0
                    locations[from_loc] = new_val

                if to_loc:
                    to_loc = str(to_loc)
                    current = float(locations.get(to_loc, 0.0))
                    locations[to_loc] = current + qty

        self._save()



    def calculate_fifo_cost(self, product_id: str, movements: List, fallback_price: float = 0.0) -> float:
        pid = self._get_full_product_id(product_id)

        batches = []
        total_cost = 0.0

        relevant = []
        for m in movements:
            if str(m.product_id) == pid:
                relevant.append(m)

        relevant.sort(key=lambda x: x.date)

        for m in relevant:
            mtype = m.movement_type.name
            qty = float(m.quantity)

            if mtype == "IN":
                if m.price is not None:
                    price = float(m.price)
                else:
                    price = float(fallback_price)

                batches.append({"qty": qty, "price": price})

            elif mtype == "OUT":
                need = qty

                while need > 0 and batches:
                    if batches[0]["qty"] <= need:
                        total_cost += batches[0]["qty"] * batches[0]["price"]
                        need -= batches[0]["qty"]
                        batches.pop(0)
                    else:
                        total_cost += need * batches[0]["price"]
                        batches[0]["qty"] -= need
                        need = 0

        return round(total_cost, 2)


    def get_total_inventory_value_fifo(self, movement_controller) -> float:
        total_inventory_value = 0.0

        movements_source = movement_controller.movements

        if isinstance(movements_source, dict):
            all_movements = []
            for key in movements_source:
                all_movements.append(movements_source[key])
        else:
            all_movements = movements_source

        for pid in self.data.get("products", {}).keys():
            prod_movements = []
            for m in all_movements:
                if str(m.product_id) == str(pid):
                    prod_movements.append(m)

            prod_movements.sort(key=lambda x: x.date)

            product_obj = self.product_controller.get_by_id(pid)
            if product_obj:
                fallback = float(product_obj.price)
            else:
                fallback = 0.0

            batches = []

            for m in prod_movements:
                m_type = m.movement_type.name
                qty = float(m.quantity)

                if m_type == "IN":
                    if m.price is not None:
                        price = float(m.price)
                    else:
                        price = fallback

                    batches.append({"qty": qty, "price": price})

                elif m_type == "OUT":
                    need = qty

                    while need > 0 and batches:
                        if batches[0]["qty"] <= need:
                            need -= batches[0]["qty"]
                            batches.pop(0)
                        else:
                            batches[0]["qty"] -= need
                            need = 0

            for b in batches:
                total_inventory_value += b["qty"] * b["price"]

        return round(total_inventory_value, 2)
