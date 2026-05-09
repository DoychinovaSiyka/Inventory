from typing import List, Dict


class InventoryController:
    def __init__(self, repository, product_controller, location_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller

        raw = self.repo.load()

        # Ако има записан инвентар – ползваме го; иначе започваме с празна структура
        self.data = raw if raw and "products" in raw else {"products": {}}

    def _save(self):
        # Записваме текущото състояние
        self.repo.save(self.data)

    def _get_full_product_id(self, input_id: str) -> str:
        # Ако е подадено съкратено ID, намираме пълното
        product = self.product_controller.get_by_id(str(input_id))
        return product.product_id if product else str(input_id)

    def _get_full_location_id(self, input_id: str) -> str:
        # Същото, но за локации
        if not input_id:
            return None
        loc = self.location_controller.get_by_id(str(input_id))
        return loc.location_id if loc else str(input_id)

    # Наличности

    def get_stock(self, product_id: str, location_id: str) -> float:
        # Съвместимост с View-тата
        return self.get_stock_by_location(product_id, location_id)

    def get_stock_by_location(self, product_id: str, location_id: str) -> float:
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid or pid not in self.data["products"]:
            return 0.0

        locations = self.data["products"][pid].get("locations", {})
        return float(locations.get(lid, 0.0))

    def get_total_stock(self, product_id: str) -> float:
        # Общо количество от всички складове
        pid = self._get_full_product_id(product_id)
        if pid not in self.data["products"]:
            return 0.0

        locations = self.data["products"][pid].get("locations", {})
        return sum(float(q) for q in locations.values())

    # Промяна на количества

    def increase_stock(self, product_id: str, quantity: float, location_id: str):
        # Добавяме количество при доставка
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid:
            return

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locs = self.data["products"][pid]["locations"]
        locs[lid] = float(locs.get(lid, 0.0)) + float(quantity)
        self._save()

    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        # Намаляваме количество при продажба
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)

        if not lid or pid not in self.data["products"]:
            return False

        locs = self.data["products"][pid]["locations"]
        current = float(locs.get(lid, 0.0))
        qty = float(quantity)

        if current < qty:
            return False

        locs[lid] = current - qty
        self._save()
        return True

    # Пълно пресмятане от движения

    def rebuild_inventory_from_movements(self, movements: List):
        # Пресмятаме инвентара от нулата по хронологията на движенията
        self.data = {"products": {}}
        sorted_moves = sorted(movements, key=lambda m: m.date)

        for m in sorted_moves:
            pid = str(m.product_id)
            qty = float(m.quantity)
            m_type = m.movement_type.name if hasattr(m.movement_type, "name") else str(m.movement_type)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locs = self.data["products"][pid]["locations"]

            if m_type == "IN" and m.location_id:
                lid = str(m.location_id)
                locs[lid] = locs.get(lid, 0.0) + qty

            elif m_type == "OUT" and m.location_id:
                lid = str(m.location_id)
                locs[lid] = max(0.0, locs.get(lid, 0.0) - qty)

            elif m_type == "MOVE":
                from_lid = str(m.from_location_id) if m.from_location_id else None
                to_lid = str(m.to_location_id) if m.to_location_id else None

                if from_lid:
                    locs[from_lid] = max(0.0, locs.get(from_lid, 0.0) - qty)
                if to_lid:
                    locs[to_lid] = locs.get(to_lid, 0.0) + qty

        self._save()

    # FIFO себестойност

    def calculate_fifo_cost(self, product_id: str, movements: List, fallback_price: float = 0.0) -> float:
        pid = self._get_full_product_id(product_id)

        # Колко е продадено общо
        total_sold = 0.0
        for m in movements:
            m_type = m.movement_type.name if hasattr(m.movement_type, "name") else str(m.movement_type)
            if str(m.product_id) == pid and m_type == "OUT":
                total_sold += float(m.quantity)

        if total_sold <= 0:
            return 0.0

        # Всички доставки по ред на постъпване
        batches = []
        for m in sorted(movements, key=lambda x: x.date):
            m_type = m.movement_type.name if hasattr(m.movement_type, "name") else str(m.movement_type)
            if str(m.product_id) == pid and m_type == "IN":
                price = float(m.price) if m.price and float(m.price) > 0 else float(fallback_price)
                batches.append({"qty": float(m.quantity), "price": price})

        # Изваждаме количествата от най-старите партиди
        total_cost = 0.0
        remaining = total_sold

        for batch in batches:
            if remaining <= 0:
                break

            take = min(batch["qty"], remaining)
            total_cost += take * batch["price"]
            remaining -= take

        # Ако продажбите са повече от доставките
        if remaining > 0:
            total_cost += remaining * fallback_price

        return round(total_cost, 2)

    # FIFO стойност на остатъка

    def get_total_inventory_value_fifo(self, movement_controller) -> float:
        # Стойност на наличностите по FIFO
        total_value = 0.0
        all_moves = movement_controller.get_all()

        for pid in self.data.get("products", {}):
            product_obj = self.product_controller.get_by_id(pid)
            fb_price = float(product_obj.price) if product_obj else 0.0

            prod_moves = sorted(
                [m for m in all_moves if str(m.product_id) == pid],
                key=lambda x: x.date
            )

            batches = []

            for m in prod_moves:
                m_type = m.movement_type.name if hasattr(m.movement_type, "name") else str(m.movement_type)
                qty = float(m.quantity)

                if m_type == "IN":
                    price = float(m.price) if m.price and float(m.price) > 0 else fb_price
                    batches.append({"qty": qty, "price": price})

                elif m_type == "OUT":
                    # Премахваме количества от най-старите партиди
                    while qty > 0 and batches:
                        if batches[0]["qty"] <= qty:
                            qty -= batches[0]["qty"]
                            batches.pop(0)
                        else:
                            batches[0]["qty"] -= qty
                            qty = 0

            total_value += sum(b["qty"] * b["price"] for b in batches)

        return round(total_value, 2)
