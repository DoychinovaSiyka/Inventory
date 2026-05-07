from typing import List

class InventoryController:
    def __init__(self, repository, product_controller, location_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller

        # Данните в JSON са с пълни UUID: { "products": { "36-char-uuid": { "locations": { "36-char-uuid": qty } } } }
        self.data = self.repo.load() or {"products": {}}

    def _save(self):
        self.repo.save(self.data)

    def _get_full_product_id(self, input_id):
        """Помощен метод: превръща кратко ID в пълно UUID."""
        product = self.product_controller.get_by_id(input_id)
        return product.product_id if product else str(input_id)

    def _get_full_location_id(self, input_id):
        location = self.location_controller.get_by_id(input_id)
        return location.location_id if location else str(input_id)

    # ОБЩО КОЛИЧЕСТВО
    def get_total_stock(self, product_id):
        pid = self._get_full_product_id(product_id)
        if pid not in self.data["products"]:
            return 0.0

        locations = self.data["products"][pid].get("locations", {})
        return sum(float(qty) for qty in locations.values())


    def increase_stock(self, product_id, quantity, location_id):
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)
        quantity = float(quantity)

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locations = self.data["products"][pid]["locations"]
        locations[lid] = locations.get(lid, 0.0) + quantity
        self._save()

    # НАМАЛЯВАНЕ НА НАЛИЧНОСТ
    def decrease_stock(self, product_id, quantity, location_id):
        pid = self._get_full_product_id(product_id)
        lid = self._get_full_location_id(location_id)
        quantity = float(quantity)

        if pid not in self.data["products"]:
            return False

        locations = self.data["products"][pid]["locations"]
        current = locations.get(lid, 0.0)
        if current < quantity:
            return False

        locations[lid] = current - quantity
        self._save()
        return True

    # ПЪЛНО ПРЕСМЯТАНЕ ОТ ДВИЖЕНИЯ
    def rebuild_inventory_from_movements(self, movements):
        self.data = {"products": {}}

        for m in movements:
            # Тук movement вече съдържа пълните ID-та в обекта си
            pid = str(m.product_id)
            qty = float(m.quantity)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locations = self.data["products"][pid]["locations"]
            m_type = m.movement_type.name

            if m_type == "IN":
                loc = m.location_id
                locations[loc] = locations.get(loc, 0.0) + qty
            elif m_type == "OUT":
                loc = m.location_id
                locations[loc] = locations.get(loc, 0.0) - qty
            elif m_type == "MOVE":
                from_loc = m.from_location_id
                to_loc = m.to_location_id
                locations[from_loc] = locations.get(from_loc, 0.0) - qty
                locations[to_loc] = locations.get(to_loc, 0.0) + qty

        self._save()

    # FIFO себестойност
    def calculate_fifo_cost(self, product_id, movements, fallback_price=0.0):
        """ Смятам себестойността на продаденото по FIFO. Подреждам всички движения по дата и
              водя списък с партиди от доставки.
              При продажба изписвам количества от най-старите налични партиди и така получавам
              реалната себестойност на продадените бройки."""

        pid = self._get_full_product_id(product_id)
        batches = []
        total_cost = 0.0

        # Филтрираме движенията
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

    # Обща стойност на склада
    def get_total_inventory_value_fifo(self, movement_controller):
        total_value = 0.0
        # Обхождаме продуктите
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
                    qty = float(m.quantity)
                    price = float(m.price) if m.price is not None else float(product.price)
                    total_purchase_expense += qty * price
                    total_in_qty += qty

            if total_in_qty > 0:
                avg_price = total_purchase_expense / total_in_qty
                total_value += current_stock * avg_price
            else:
                total_value += current_stock * float(product.price)

        return total_value