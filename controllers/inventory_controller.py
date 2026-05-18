from typing import Optional, List
from validators.inventory_validator import InventoryValidator


class InventoryController:
    def __init__(self, repository, product_controller, location_controller, movement_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller
        self.movement_controller = movement_controller

        #  ЗАРЕЖДАНЕ - Случва се тук в началото
        raw_data = self.repo.load()

        # Проверка и подготовка на данните директно в конструктора
        if isinstance(raw_data, dict) and "products" in raw_data:
            self._data = raw_data
        else:
            self._data = {"products": {}}

        # Пресмятаме инвентара
        self.update_inventory_from_movements(self.movement_controller.movements)

    # Капсулиран метод, който се вика само при нужда
    def _save(self):
        summary = self.build_inventory()
        self.repo.save(summary)



    # Намираме ID на продукт по въведен текст
    def _product_id(self, user_input: str) -> Optional[str]:
        if not user_input:
            return None

        user_input = str(user_input).strip()
        if user_input in self.data.get("products", {}):
            return user_input


        for full_id in self.data.get("products", {}).keys():
            if full_id.startswith(user_input):
                return full_id


        for p in self.product_controller.get_all():
            if user_input.lower() == p.name.lower() or str(p.product_id).startswith(user_input):
                return str(p.product_id)

        return user_input

    # Намираме ID на склад
    def _location_id(self, user_input: str) -> Optional[str]:
        if not user_input:
            return None

        user_input = str(user_input).strip()

        loc = self.location_controller.get_by_id(user_input)
        if loc:
            return str(loc.location_id)

        for l in self.location_controller.get_all():
            if str(l.location_id).startswith(user_input):
                return str(l.location_id)

        return user_input

    # Увеличаваме наличността
    def increase_stock(self, product_id: str, quantity: float, location_id: str):
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        qty = InventoryValidator.parse_and_validate_number(quantity, "Количество за заприходяване")

        # Ако продуктът го няма – създаваме го
        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locations = self.data["products"][pid]["locations"]
        current = float(locations.get(lid, 0.0))

        # Добавяме новото количество
        locations[lid] = round(current + qty, 3)

    # Намаляваме наличността
    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        qty = InventoryValidator.parse_and_validate_number(quantity, "Количество за изписване")

        # Проверяваме дали имаме достатъчно наличност
        current_stock = self.get_stock(pid, lid)

        product_obj = self.product_controller.get_by_id(pid)
        p_name = product_obj.name if product_obj else pid

        InventoryValidator.validate_stock_availability(qty, current_stock, p_name)

        # Намаляваме количеството
        locations = self.data["products"][pid]["locations"]
        locations[lid] = round(current_stock - qty, 3)
        return True



    # Преместване на стока между складове
    def move_stock(self, product_id: str, quantity: float, from_location_id: str, to_location_id: str) -> bool:
        InventoryValidator.validate_move_locations(from_location_id, to_location_id)

        pid = self._product_id(product_id)
        qty = InventoryValidator.parse_and_validate_number(quantity, "Количество за трансфер")

        # Първо вадим от стария склад, после добавяме в новия
        if self.decrease_stock(pid, qty, from_location_id):
            self.increase_stock(pid, qty, to_location_id)
            return True
        return False

    # Общо количество от продукт - във всички складове
    def get_total_stock(self, product_id: str) -> float:
        pid = self._product_id(product_id)

        products = self.data.get("products", {})
        product_info = products.get(pid, {})

        locations = product_info.get("locations", {})
        total = 0.0

        for qty in locations.values():
            try:
                total += float(qty)
            except:
                total += 0.0

        return total



    # Количество от продукт в конкретен склад
    def get_stock(self, product_id, location_id):
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        products = self.data.get("products", {})

        if pid not in products:
            return 0.0

        product_info = products[pid]
        locations = product_info.get("locations", {})

        if lid not in locations:
            return 0.0

        try:
            return float(locations[lid])
        except:
            return 0.0



    def build_inventory(self):
        rows = []

        for pid, p_info in self.data.get("products", {}).items():
            product_obj = self.product_controller.get_by_id(pid)
            if not product_obj:
                continue


            total = self.get_total_stock(pid)

            # Разпределение по складове
            warehouse_map = {}
            for lid, qty in p_info.get("locations", {}).items():
                loc = self.location_controller.get_by_id(lid)
                name = loc.name if loc else f"Склад {lid}"
                warehouse_map[name] = float(qty)

            # Взимаме всички движения за този продукт
            moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            in_moves = [m for m in moves if m.movement_type.name == "IN"]
            out_moves = [m for m in moves if m.movement_type.name == "OUT"]

            delivered = sum(float(m.quantity) for m in in_moves)
            sold = sum(float(m.quantity) for m in out_moves)

            in_prices = [float(m.price) for m in in_moves if m.price]
            out_prices = [float(m.price) for m in out_moves if m.price]

            avg_in = round(sum(in_prices) / len(in_prices), 2) if in_prices else 0.0
            avg_out = round(sum(out_prices) / len(out_prices), 2) if out_prices else 0.0

            expense = round(delivered * avg_in, 2)
            revenue = round(sold * avg_out, 2)


            if moves:
                last = sorted(moves, key=lambda x: x.date)[-1]
                last_movement = f"{last.movement_type.name} - {str(last.date)[:19]}"
            else:
                last_movement = "Няма движения"

            # Добавяме реда в JSON структурата
            rows.append({ "product_id": pid, "product_name": product_obj.name,
                          "unit": product_obj.unit, "total": total, "warehouses": warehouse_map,
                          "delivered": delivered, "sold": sold, "avg_in_price": avg_in,
                          "avg_out_price": avg_out, "expense": expense, "revenue": revenue,
                          "last_movement": last_movement})

        return {"products": rows, "summary": {"total_products": len(rows)}}



    # Пресмятаме инвентара от всички движения
    def update_inventory_from_movements(self, movements):
        self.data = {"products": {}}
        sorted_movements = sorted(movements, key=lambda x: x.date)

        for mv in sorted_movements:
            mtype = mv.movement_type.name
            pid = str(mv.product_id)
            qty = float(mv.quantity)

            # Ако продуктът го няма – създаваме го
            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locations = self.data["products"][pid]["locations"]

            # Заприхождаване
            if mtype == "IN":
                lid = str(mv.location_id)
                current = locations.get(lid, 0.0)
                locations[lid] = round(current + qty, 3)

            # Изписване
            elif mtype == "OUT":
                lid = str(mv.location_id)
                current = locations.get(lid, 0.0)
                locations[lid] = round(current - qty, 3)

            # Трансфер между складове
            elif mtype == "MOVE":
                from_lid = str(mv.from_location_id)
                to_lid = str(mv.to_location_id)

                # Вадим от стария склад
                locations[from_lid] = round(locations.get(from_lid, 0.0) - qty, 3)
                # Добавяме в новия
                locations[to_lid] = round(locations.get(to_lid, 0.0) + qty, 3)


        self._save()