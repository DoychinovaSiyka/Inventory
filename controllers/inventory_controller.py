from typing import List, Dict


class InventoryController:
    def __init__(self, repository, product_controller, location_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller

        raw = self.repo.load()

        # Синхронизираме структурата на данните
        if raw and "products" in raw:
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

        return str(input_id)

    def get_stock_by_location(self, product_id: str, location_id: str) -> float:
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid:
            return 0.0

        if pid not in self.data["products"]:
            return 0.0

        locations = self.data["products"][pid].get("locations", {})

        if lid in locations:
            return float(locations[lid])

        return 0.0

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

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locations = self.data["products"][pid]["locations"]

        current = float(locations.get(lid, 0.0))
        new_value = current + float(quantity)

        locations[lid] = new_value
        self._save()

    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid:
            return False

        if pid not in self.data["products"]:
            return False

        locations = self.data["products"][pid]["locations"]
        current = float(locations.get(lid, 0.0))
        qty_to_remove = float(quantity)

        if current < qty_to_remove:
            return False

        locations[lid] = current - qty_to_remove
        self._save()
        return True

    def rebuild_inventory_from_movements(self, movements: List):
        """Пълно преизчисляване на база хронологията на движенията."""

        self.data = {"products": {}}

        # Сортираме движенията ръчно по дата
        sorted_moves = movements[:]
        sorted_moves.sort(key=lambda m: m.date)

        for m in sorted_moves:
            pid = str(m.product_id)
            qty = float(m.quantity)
            m_type = m.movement_type.name

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locations = self.data["products"][pid]["locations"]

            if m_type == "IN" and m.location_id:
                lid = str(m.location_id)
                current = float(locations.get(lid, 0.0))
                locations[lid] = current + qty

            elif m_type == "OUT" and m.location_id:
                lid = str(m.location_id)
                current = float(locations.get(lid, 0.0))
                new_value = current - qty
                if new_value < 0:
                    new_value = 0.0
                locations[lid] = new_value

            elif m_type == "MOVE":
                from_lid = str(m.from_location_id) if m.from_location_id else None
                to_lid = str(m.to_location_id) if m.to_location_id else None

                if from_lid:
                    current = float(locations.get(from_lid, 0.0))
                    new_value = current - qty
                    if new_value < 0:
                        new_value = 0.0
                    locations[from_lid] = new_value

                if to_lid:
                    current = float(locations.get(to_lid, 0.0))
                    locations[to_lid] = current + qty

        self._save()

    def calculate_fifo_cost(self, product_id: str, movements: List, fallback_price: float = 0.0) -> float:
        """Пресмята себестойността на продадените стоки по FIFO метода."""

        pid = self._get_full_product_id(product_id)
        batches = []
        total_cost = 0.0

        # Филтрираме движенията за този продукт
        relevant = []
        for m in movements:
            if str(m.product_id) == pid:
                relevant.append(m)


        relevant.sort(key=lambda m: m.date)

        for m in relevant:
            qty = float(m.quantity)

            if m.movement_type.name == "IN":
                if m.price is not None:
                    price = float(m.price)
                else:
                    price = float(fallback_price)

                batches.append({"qty": qty, "price": price})

            elif m.movement_type.name == "OUT":
                need = qty

                while need > 0 and batches:
                    first = batches[0]

                    if first["qty"] <= need:
                        total_cost += first["qty"] * first["price"]
                        need -= first["qty"]
                        batches.pop(0)
                    else:
                        total_cost += need * first["price"]
                        first["qty"] -= need
                        need = 0

        return round(total_cost, 2)

    def get_total_inventory_value_fifo(self, movement_controller) -> float:
        """Пресмята стойността на текущата наличност в склада по FIFO."""

        total_value = 0.0
        all_movements = movement_controller.get_all()

        for pid in self.data.get("products", {}).keys():
            product_obj = self.product_controller.get_by_id(pid)

            if product_obj:
                fallback = float(product_obj.price)
            else:
                fallback = 0.0

            # Събираме движенията за този продукт
            prod_moves = []
            for m in all_movements:
                if str(m.product_id) == pid:
                    prod_moves.append(m)


            prod_moves.sort(key=lambda m: m.date)
            batches = []

            for m in prod_moves:
                qty = float(m.quantity)

                if m.movement_type.name == "IN":
                    if m.price is not None:
                        price = float(m.price)
                    else:
                        price = fallback

                    batches.append({"qty": qty, "price": price})

                elif m.movement_type.name == "OUT":
                    need = qty

                    while need > 0 and batches:
                        first = batches[0]

                        if first["qty"] <= need:
                            need -= first["qty"]
                            batches.pop(0)
                        else:
                            first["qty"] -= need
                            need = 0

            # Сумираме стойността на останалите партиди
            for b in batches:
                total_value += b["qty"] * b["price"]

        return round(total_value, 2)
