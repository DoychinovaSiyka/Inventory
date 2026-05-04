from typing import List
from storage.json_repository import JSONRepository


class InventoryController:
    def __init__(self, repository, product_controller, movement_controller, location_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.location_controller = location_controller
        self.data = self.repo.load() or {"products": {}}

        # Зареждане на инвентара
        if not self.movement_controller.movements:
            print("Няма движения – зареждам началните количества.")
            all_locations = self.location_controller.get_all()
            if all_locations:
                default_location = all_locations[0].location_id
                self.auto_seed_initial_stock(default_location)
        else:
            print("Има движения – възстановявам инвентара.")
            self.rebuild_inventory_from_movements(self.movement_controller.movements)

    def _save(self):
        self.repo.save(self.data)

    # СМЯТА ОБЩОТО ОТ locations
    def get_total_stock(self, product_id):
        product_id = str(product_id)
        if product_id not in self.data["products"]:
            return 0.0

        locations = self.data["products"][product_id].get("locations", {})
        total = 0.0
        for qty in locations.values():
            total += float(qty)
        return total

    # НАЧАЛНО ЗАРЕЖДАНЕ
    def auto_seed_initial_stock(self, default_location):
        for product in self.product_controller.get_all():

            # Проверяваме дали продуктът има начално количество
            if product.quantity and product.quantity > 0:

                pid = str(product.product_id)

                if pid not in self.data["products"]:
                    self.data["products"][pid] = {"locations": {}}

                locations = self.data["products"][pid]["locations"]

                current = locations.get(default_location, 0)
                locations[default_location] = current + float(product.quantity)

        self._save()

    # Увеличаване на наличност
    def increase_stock(self, product_id, quantity, location_id):
        product_id = str(product_id)
        quantity = float(quantity)

        if product_id not in self.data["products"]:
            self.data["products"][product_id] = {"locations": {}}

        locations = self.data["products"][product_id]["locations"]
        current = locations.get(location_id, 0)
        locations[location_id] = current + quantity

        self._save()

    # НАМАЛЯВАНЕ НА НАЛИЧНОСТ
    def decrease_stock(self, product_id, quantity, location_id):
        product_id = str(product_id)
        quantity = float(quantity)

        if self.get_total_stock(product_id) < quantity:
            return False

        if product_id not in self.data["products"]:
            self.data["products"][product_id] = {"locations": {}}

        locations = self.data["products"][product_id]["locations"]
        current = locations.get(location_id, 0)
        locations[location_id] = current - quantity

        self._save()
        return True

    # ПЪЛНО ПРЕСМЯТАНЕ ОТ ДВИЖЕНИЯ
    def rebuild_inventory_from_movements(self, movements):
        self.data = {"products": {}}

        for m in movements:
            pid = str(m.product_id)
            qty = float(m.quantity)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locations = self.data["products"][pid]["locations"]
            m_type = m.movement_type.name

            if m_type == "IN":
                loc = m.location_id
                current = locations.get(loc, 0)
                locations[loc] = current + qty

            elif m_type == "OUT":
                loc = m.location_id
                current = locations.get(loc, 0)
                locations[loc] = current - qty

            elif m_type == "MOVE":
                from_loc = m.from_location_id
                to_loc = m.to_location_id

                current_from = locations.get(from_loc, 0)
                locations[from_loc] = current_from - qty

                current_to = locations.get(to_loc, 0)
                locations[to_loc] = current_to + qty

        self._save()

    # FIFO себестойност
    def calculate_fifo_cost(self, product_id, movements, fallback_price=0.0):
        """ Смятам себестойността на продаденото по FIFO. Подреждам всички движения по дата и
        водя списък с партиди от доставки.
        При продажба изписвам количества от най-старите налични партиди и така получавам
        реалната себестойност на продадените бройки."""
        product_id = str(product_id)
        batches = []
        total_cost = 0.0

        relevant = []
        for m in movements:
            if str(m.product_id) == product_id:
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

    # Къде има продукт
    def get_warehouses_with_product(self, product_name):
        """ Връща списък от (warehouse_id, quantity) за всички складове, в които продуктът съществува с количество > 0."""
        result = []

        for pid, pdata in self.data.get("products", {}).items():
            product = self.product_controller.get_by_id(pid)
            if not product:
                continue

            if product.name.lower() == product_name.lower():
                locations = pdata.get("locations", {})
                for warehouse_id, qty in locations.items():
                    if qty > 0:
                        result.append((warehouse_id, qty))
                return result

        return []

    # Обща стойност на склада
    def get_total_inventory_value_fifo(self, movement_controller):
        """ Изчислява общата стойност на целия склад на база реалните доставки (FIFO/Средна цена)."""
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
                    qty = float(m.quantity)
                    if m.price is not None:
                        price = float(m.price)
                    else:
                        price = float(product.price)

                    total_purchase_expense += qty * price
                    total_in_qty += qty

            if total_in_qty > 0:
                avg_price = total_purchase_expense / total_in_qty
                total_value += current_stock * avg_price
            else:
                total_value += current_stock * float(product.price)

        return total_value
