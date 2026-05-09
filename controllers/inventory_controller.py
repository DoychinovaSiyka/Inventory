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
        return product.product_id if product else str(input_id)

    def _get_full_location_id(self, input_id: str) -> str:
        if not input_id:
            return None
        loc = self.location_controller.get_by_id(str(input_id))
        return loc.location_id if loc else str(input_id)

    def get_stock(self, product_id: str, location_id: str) -> float:
        """Помощен метод за съвместимост с View-тата."""
        return self.get_stock_by_location(product_id, location_id)

    def get_stock_by_location(self, product_id: str, location_id: str) -> float:
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid or pid not in self.data["products"]:
            return 0.0

        locations = self.data["products"][pid].get("locations", {})
        return float(locations.get(lid, 0.0))

    def get_total_stock(self, product_id: str) -> float:
        pid = self._get_full_product_id(product_id)
        if pid not in self.data["products"]:
            return 0.0

        locations = self.data["products"][pid].get("locations", {})
        return sum(float(qty) for qty in locations.values())

    def increase_stock(self, product_id: str, quantity: float, location_id: str):
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid:
            return

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locations = self.data["products"][pid]["locations"]
        locations[lid] = float(locations.get(lid, 0.0)) + float(quantity)
        self._save()

    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid or pid not in self.data["products"]:
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
        sorted_moves = sorted(movements, key=lambda m: m.date)

        for m in sorted_moves:
            pid = str(m.product_id)
            qty = float(m.quantity)
            m_type = m.movement_type.name if hasattr(m.movement_type, 'name') else str(m.movement_type)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locations = self.data["products"][pid]["locations"]

            if m_type == "IN" and m.location_id:
                lid = str(m.location_id)
                locations[lid] = locations.get(lid, 0.0) + qty
            elif m_type == "OUT" and m.location_id:
                lid = str(m.location_id)
                locations[lid] = max(0.0, locations.get(lid, 0.0) - qty)
            elif m_type == "MOVE":
                from_lid = str(m.from_location_id) if m.from_location_id else None
                to_lid = str(m.to_location_id) if m.to_location_id else None
                if from_lid:
                    locations[from_lid] = max(0.0, locations.get(from_lid, 0.0) - qty)
                if to_lid:
                    locations[to_lid] = locations.get(to_lid, 0.0) + qty

        self._save()

    def calculate_fifo_cost(self, product_id: str, movements: List, fallback_price: float = 0.0) -> float:
        """Пресмята себестойността САМО на продадените количества по FIFO."""
        pid = self._get_full_product_id(product_id)

        # 1. Намираме колко общо е продадено (OUT)
        total_sold = 0.0
        for m in movements:
            m_type = m.movement_type.name if hasattr(m.movement_type, 'name') else str(m.movement_type)
            if str(m.product_id) == pid and m_type == "OUT":
                total_sold += float(m.quantity)

        if total_sold <= 0:
            return 0.0

        # 2. Събираме всички доставки (IN) като партиди
        batches = []
        for m in sorted(movements, key=lambda x: x.date):
            m_type = m.movement_type.name if hasattr(m.movement_type, 'name') else str(m.movement_type)
            if str(m.product_id) == pid and m_type == "IN":
                price = float(m.price) if m.price is not None else float(fallback_price)
                batches.append({"qty": float(m.quantity), "price": price})

        # 3. Изчисляваме себестойността само за продаденото количество
        total_cost = 0.0
        remaining_to_calculate = total_sold

        for batch in batches:
            if remaining_to_calculate <= 0:
                break

            take_qty = min(batch["qty"], remaining_to_calculate)
            total_cost += take_qty * batch["price"]
            remaining_to_calculate -= take_qty

        return round(total_cost, 2)

    def get_total_inventory_value_fifo(self, movement_controller) -> float:
        """Пресмята стойността на това, което ОСТАВА в склада в момента."""
        total_value = 0.0
        all_movements = movement_controller.get_all()

        for pid in self.data.get("products", {}).keys():
            product_obj = self.product_controller.get_by_id(pid)
            fb_price = float(product_obj.price) if product_obj else 0.0

            prod_moves = sorted([m for m in all_movements if str(m.product_id) == pid], key=lambda x: x.date)
            batches = []

            for m in prod_moves:
                m_type = m.movement_type.name if hasattr(m.movement_type, 'name') else str(m.movement_type)
                qty = float(m.quantity)

                if m_type == "IN":
                    price = float(m.price) if m.price is not None else fb_price
                    batches.append({"qty": qty, "price": price})
                elif m_type == "OUT":
                    while qty > 0 and batches:
                        if batches[0]["qty"] <= qty:
                            qty -= batches[0]["qty"]
                            batches.pop(0)
                        else:
                            batches[0]["qty"] -= qty
                            qty = 0

            total_value += sum(b["qty"] * b["price"] for b in batches)

        return round(total_value, 2)