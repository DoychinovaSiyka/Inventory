from typing import List, Dict


class InventoryController:
    def __init__(self, repository, product_controller, location_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller
        # Структура в JSON: { "products": { "pid": { "locations": { "lid": qty } } } }
        self.data = self.repo.load() or {"products": {}}

    def _save(self):
        """Записва текущото състояние в хранилището."""
        self.repo.save(self.data)

    def _get_full_product_id(self, input_id: str) -> str:
        product = self.product_controller.get_by_id(str(input_id))
        return product.product_id if product else str(input_id)

    def _get_full_location_id(self, input_id: str) -> str:
        if not input_id: return None
        location = self.location_controller.get_by_id(str(input_id))
        return location.location_id if location else str(input_id)

    def get_total_stock(self, product_id: str) -> float:
        """Връща общата наличност на продукт във всички складове."""
        pid = self._get_full_product_id(product_id)
        if pid not in self.data["products"]:
            return 0.0
        locations = self.data["products"][pid].get("locations", {})
        return sum(float(qty) for qty in locations.values())

    def increase_stock(self, product_id: str, quantity: float, location_id: str):
        """Увеличава наличността в конкретна локация."""
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)
        if not lid: return

        qty_to_add = float(quantity)
        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locations = self.data["products"][pid]["locations"]
        locations[lid] = float(locations.get(lid, 0.0)) + qty_to_add
        self._save()

    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        """Намалява наличността. Връща False, ако няма достатъчно количество."""
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)
        if not lid: return False

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
        """Пълно реконструиране на склада въз основа на историята.Защита срещу отрицателни наличности."""
        self.data = {"products": {}}
        # Сортираме по дата, за да гарантираме хронологична реконструкция
        sorted_movements = sorted(movements, key=lambda x: x.date)

        for m in sorted_movements:
            pid = str(m.product_id)
            qty = float(m.quantity)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locations = self.data["products"][pid]["locations"]
            m_type = m.movement_type.name

            if m_type == "IN":
                loc = str(m.location_id)
                locations[loc] = float(locations.get(loc, 0.0)) + qty
            elif m_type == "OUT":
                loc = str(m.location_id)
                # Защита: наличността не може да бъде под 0
                locations[loc] = max(0.0, float(locations.get(loc, 0.0)) - qty)
            elif m_type == "MOVE":
                from_loc = str(m.from_location_id)
                to_loc = str(m.to_location_id)
                locations[from_loc] = max(0.0, float(locations.get(from_loc, 0.0)) - qty)
                locations[to_loc] = float(locations.get(to_loc, 0.0)) + qty

        self._save()

    def calculate_fifo_cost(self, product_id: str, movements: List, fallback_price: float = 0.0) -> float:
        """Изчислява себестойността на продаденото по метода FIFO."""
        pid = self._get_full_product_id(product_id)
        batches = []
        total_cost = 0.0

        relevant = [m for m in movements if str(m.product_id) == pid]
        relevant.sort(key=lambda x: x.date)

        for m in relevant:
            mtype = m.movement_type.name
            qty = float(m.quantity)
            if mtype == "IN":
                price = float(m.price) if m.price is not None else float(fallback_price)
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
        """Изчислява общата парична стойност на целия склад чрез FIFO симулация."""
        total_inventory_value = 0.0
        all_movements = movement_controller.movements

        for pid in self.data.get("products", {}).keys():
            prod_movements = [m for m in all_movements if str(m.product_id) == str(pid)]
            prod_movements.sort(key=lambda x: x.date)
            product_obj = self.product_controller.get_by_id(pid)
            fallback = float(product_obj.price) if product_obj else 0.0

            batches = []
            for m in prod_movements:
                m_type = m.movement_type.name
                qty = float(m.quantity)

                if m_type == "IN":
                    price = float(m.price) if m.price is not None else fallback
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

            # Стойността на останалите партиди е стойността на наличността
            for b in batches:
                total_inventory_value += b["qty"] * b["price"]

        return round(total_inventory_value, 2)