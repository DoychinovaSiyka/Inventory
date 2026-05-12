from typing import List, Dict, Optional
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """Управлява наличностите в реално време и поддържа финансови изчисления."""

    def __init__(self, repository, product_controller, location_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller

        raw = self.repo.load()
        self.data = raw if (raw and "products" in raw) else {"products": {}}

    def _save(self) -> None:
        """Записва текущото състояние в хранилището."""
        self.repo.save(self.data)

    def get_stock(self, product_id: str, location_id: str) -> float:
        pid = str(product_id or "").strip()
        lid = str(location_id or "").strip()

        #  продуктът дали съществува в инвентара
        if pid not in self.data.get("products", {}):
            return 0.0

        # Проверяваме дали локацията е валидна
        if lid == "":
            return 0.0

        # Всички локации за този продукт
        product_info = self.data["products"][pid]
        locations = product_info.get("locations", {})

        # Количеството за конкретната локация
        raw_qty = locations.get(lid, 0.0)
        return InventoryValidator.parse_and_validate_number(raw_qty)



    def get_total_stock(self, product_id: str) -> float:
        """Връща общото количество от продукта във всички складове."""

        pid = str(product_id or "").strip()
        if pid not in self.data.get("products", {}):
            return 0.0

        product_info = self.data["products"][pid]
        locations = product_info.get("locations", {})
        total = 0.0


        for loc_id in locations:
            qty = locations[loc_id]
            qty = InventoryValidator.parse_and_validate_number(qty)
            total += qty

        return total

    def increase_stock(self, product_id: str, quantity: float, location_id: str) -> None:
        """Увеличава наличността по прост и разбираем начин."""

        pid = str(product_id or "").strip()
        lid = str(location_id or "").strip()

        if lid == "":
            return


        qty_to_add = InventoryValidator.parse_and_validate_number(quantity, "Количество")

        # Ако продуктът не съществува - създаваме го
        if pid not in self.data.get("products", {}):
            self.data["products"][pid] = {"locations": {}}

        product_info = self.data["products"][pid]
        locations = product_info.get("locations", {})


        current_qty = locations.get(lid, 0.0)
        current_qty = InventoryValidator.parse_and_validate_number(current_qty)
        new_qty = current_qty + qty_to_add
        locations[lid] = round(new_qty, 2)

        self._save()

    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = str(product_id or "").strip()
        lid = str(location_id or "").strip()
        if pid not in self.data.get("products", {}):
            return False

        if lid == "":
            return False


        qty_to_remove = InventoryValidator.parse_and_validate_number(quantity, "Количество")
        product_info = self.data["products"][pid]
        locations = product_info.get("locations", {})


        current_qty = locations.get(lid, 0.0)
        current_qty = InventoryValidator.parse_and_validate_number(current_qty)


        prod_obj = self.product_controller.get_by_id(pid)
        loc_obj = self.location_controller.get_by_id(lid)

        if prod_obj:
            product_name = prod_obj.name
        else:
            product_name = pid

        if loc_obj:
            location_name = loc_obj.name
        else:
            location_name = lid


        try:
            InventoryValidator.validate_stock_availability(product_name, qty_to_remove, current_qty, location_name)
        except ValueError:
            return False

        new_qty = current_qty - qty_to_remove
        locations[lid] = round(new_qty, 2)

        self._save()
        return True



    def rebuild_inventory_from_movements(self, movements: List) -> None:
        """Преизчислява целия инвентар от историята."""
        self.data = {"products": {}}

        sorted_moves = sorted(movements, key=lambda m: m.date)
        for m in sorted_moves:
            pid = str(m.product_id)
            qty = InventoryValidator.parse_and_validate_number(m.quantity)

            try:
                m_type = m.movement_type.name
            except Exception:
                m_type = str(m.movement_type)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locs = self.data["products"][pid]["locations"]

            if m_type == "IN" and m.location_id:
                locs[m.location_id] = round(locs.get(m.location_id, 0.0) + qty, 2)

            elif m_type == "OUT" and m.location_id:
                current = locs.get(m.location_id, 0.0)
                locs[m.location_id] = round(max(0.0, current - qty), 2)

            elif m_type == "MOVE":
                # Добавяме проверка за еднакви складове при преместване
                if m.from_location_id and m.to_location_id:
                    try:
                        InventoryValidator.validate_move_locations(m.from_location_id, m.to_location_id)

                        # Намаляваме от източника
                        curr_from = locs.get(m.from_location_id, 0.0)
                        locs[m.from_location_id] = round(max(0.0, curr_from - qty), 2)

                        # Увеличаваме в целта
                        curr_to = locs.get(m.to_location_id, 0.0)
                        locs[m.to_location_id] = round(curr_to + qty, 2)
                    except ValueError:
                        continue  # Прескачаме некоректни премествания

        self._save()

    def sort_products_by_quantity(self, reverse=True):
        """Връща продуктите, сортирани по общо количество."""
        products = self.product_controller.get_all()
        return sorted(products, key=lambda p: self.get_total_stock(p.product_id), reverse=reverse)

    def calculate_fifo_cost(self, product_id: str, movements: List, fallback_price: float = 0.0) -> float:
        """Пресмята себестойността по FIFO, без магически атрибути и без getattr."""


        pid, _ = self._resolve_ids(product_id)

        #  колко бройки са продадени
        total_sold = 0.0
        for m in movements:
            m_type = str(m.movement_type).upper()

            if str(m.product_id) == pid and m_type == "OUT":
                qty = InventoryValidator.parse_and_validate_number(m.quantity)
                total_sold += qty


        if total_sold <= 0:
            return 0.0

        # Събираме всички входящи партиди
        batches = []
        sorted_moves = sorted(movements, key=lambda x: x.date)

        for m in sorted_moves:
            m_type = str(m.movement_type).upper()

            if str(m.product_id) == pid and m_type == "IN":
                if m.price:
                    price = InventoryValidator.parse_and_validate_number(m.price)
                else:
                    price = fallback_price

                qty = InventoryValidator.parse_and_validate_number(m.quantity)

                # Добавяме партида
                batches.append({"qty": qty, "price": price})


        # изчисляваме себестойността по FIFO
        total_cost = 0.0
        remaining = total_sold

        for batch in batches:
            if remaining <= 0:
                break

            take = batch["qty"]
            if take > remaining:
                take = remaining

            total_cost += take * batch["price"]
            remaining -= take


        if remaining > 0:
            total_cost += remaining * fallback_price

        return round(total_cost, 2)

    def get_total_inventory_value_fifo(self, movement_controller) -> float:
        """Изчислява общата стойност на склада по FIFO, без магически атрибути."""
        total_value = 0.0
        all_moves = movement_controller.get_all()

        # Минаваме през всички продукти, които са записани в инвентара
        for pid in self.data.get("products", {}):
            product_obj = self.product_controller.get_by_id(pid)
            if product_obj:
                fallback_price = float(product_obj.price)
            else:
                fallback_price = 0.0

            product_moves = []
            for m in all_moves:
                if str(m.product_id) == pid:
                    product_moves.append(m)

            product_moves.sort(key=lambda x: x.date)

            # държим FIFO партидите
            batches = []

            for m in product_moves:
                m_type = str(m.movement_type).upper()

                qty = InventoryValidator.parse_and_validate_number(m.quantity)

                if m_type == "IN":
                    # Ако има цена → ползваме я, иначе fallback
                    if m.price:
                        price = InventoryValidator.parse_and_validate_number(m.price)
                    else:
                        price = fallback_price

                    batches.append({"qty": qty, "price": price})


                elif m_type == "OUT":
                    remaining = qty
                    while remaining > 0 and batches:
                        first_batch = batches[0]
                        if first_batch["qty"] <= remaining:
                            remaining -= first_batch["qty"]
                            batches.pop(0)
                        else:
                            first_batch["qty"] -= remaining
                            remaining = 0


            for batch in batches:
                total_value += batch["qty"] * batch["price"]

        return round(total_value, 2)
