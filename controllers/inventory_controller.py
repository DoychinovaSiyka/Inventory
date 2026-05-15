from typing import Optional, List
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """Управлява наличностите в реално време."""

    def __init__(self, repository, product_controller, location_controller, movement_controller):
        self.repo = repository
        self.product_controller = product_controller
        self.location_controller = location_controller
        self.movement_controller = movement_controller

        self.data = self._load()

        # Първоначално изграждане на наличностите от историята
        self.update_inventory_from_movements(self.movement_controller.movements)




    def _load(self):
        data = self.repo.load()

        if not isinstance(data, dict):
            return {"products": {}}

        if "products" not in data or not isinstance(data["products"], dict):
            data["products"] = {}

        return data



    def _save(self):
        summary = self._build_inventory()
        self.repo.save(summary)



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




    def increase_stock(self, product_id: str, quantity: float, location_id: str):
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)

        if "products" not in self.data:
            self.data["products"] = {}

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}


        locations = self.data["products"][pid]["locations"]

        # Текущо количество
        if lid in locations:
            try:
                current = float(locations[lid])
            except:
                current = 0.0
        else:
            current = 0.0


        try:
            qty = float(quantity)
        except:
            qty = 0.0

        new_value = current + qty
        locations[lid] = round(new_value, 2)





    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid = self._product_id(product_id)
        lid = self._location_id(location_id)
        products = self.data.get("products", {})
        if pid not in products:
            return False

        product_info = products[pid]
        locations = product_info.get("locations", {})
        if lid not in locations:
            return False

        try:
            current = float(locations[lid])
        except:
            current = 0.0

        try:
            qty = float(quantity)
        except:
            qty = 0.0

        if current < qty:
            return False

        new_value = current - qty
        locations[lid] = round(new_value, 2)

        return True





    def move_stock(self, product_id: str, quantity: float, from_location_id: str, to_location_id: str) -> bool:
        pid = self._product_id(product_id)
        from_lid = self._location_id(from_location_id)
        to_lid = self._location_id(to_location_id)

        if not self.decrease_stock(pid, quantity, from_lid):
            return False

        self.increase_stock(pid, quantity, to_lid)
        return True



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





    def calculate_fifo_cost(self, product_id: str, movements: List, fallback_price: float = 0.0) -> float:
        pid = self._product_id(product_id)

        # смятаме колко е продадено общо
        total_sold = 0.0
        for m in movements:
            if str(m.product_id) == pid and m.movement_type.name == "OUT":
                total_sold += float(m.quantity)


        if total_sold <= 0:
            return 0.0

        # Събираме всички доставки като партиди
        batches = []
        sorted_moves = sorted(movements, key=lambda x: x.date)

        for m in sorted_moves:
            if str(m.product_id) == pid and m.movement_type.name == "IN":
                if m.price and float(m.price) > 0:
                    price = float(m.price)
                else:
                    price = float(fallback_price)

                qty = float(m.quantity)
                batches.append({"qty": qty, "price": price})


        total_cost = 0.0
        remaining = total_sold

        for batch in batches:
            if remaining <= 0:
                break

            # Колко можем да вземем от тази партида
            if batch["qty"] < remaining:
                take = batch["qty"]
            else:
                take = remaining

            total_cost += take * batch["price"]
            remaining -= take

        # Ако не стигат партидите - дописваме с fallback цена
        if remaining > 0:
            total_cost += remaining * float(fallback_price)

        return round(total_cost, 2)





    def _build_inventory(self):
        rows = []

        for pid, p_info in self.data.get("products", {}).items():
            product_obj = self.product_controller.get_by_id(pid)
            if not product_obj:
                continue

            total = self.get_total_stock(pid)
            if total <= 0:
                continue

            warehouse_map = {}
            for lid, qty in p_info.get("locations", {}).items():
                if qty <= 0:
                    continue

                loc = self.location_controller.get_by_id(lid)
                name = loc.name if loc else "Неизвестен склад"
                warehouse_map[name] = qty

            movements = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            delivered = sum(float(m.quantity) for m in movements if m.movement_type.name == "IN")
            sold = sum(float(m.quantity) for m in movements if m.movement_type.name == "OUT")

            in_prices = [float(m.price) for m in movements if m.movement_type.name == "IN" and m.price]
            out_prices = [float(m.price) for m in movements if m.movement_type.name == "OUT" and m.price]

            avg_in = round(sum(in_prices) / len(in_prices), 2) if in_prices else 0.0
            avg_out = round(sum(out_prices) / len(out_prices), 2) if out_prices else 0.0

            expense = round(delivered * avg_in, 2)
            revenue = round(sold * avg_out, 2)


            if movements:
                last = sorted(movements, key=lambda x: x.date)[-1]
                last_movement = f"{last.movement_type.name} - {last.date}"
            else:
                last_movement = "Няма движения"

            rows.append({"product": product_obj.name, "unit": product_obj.unit, "total": total,
                         "warehouses": warehouse_map, "delivered": delivered, "sold": sold,
                         "avg_in_price": avg_in, "avg_out_price": avg_out, "expense": expense,
                         "revenue": revenue, "last_movement": last_movement})

        return {"products": rows, "summary": {"total_products": len(rows)}}





    def update_inventory_from_movements(self, movements):
        self.data = {"products": {}}

        for mv in movements:
            mtype = mv.movement_type.name

            if mtype == "MOVE":
                if mv.from_location_id is None or mv.to_location_id is None:
                    continue
                self.move_stock(mv.product_id, mv.quantity, mv.from_location_id, mv.to_location_id)
                continue

            if mv.location_id is None:
                continue

            if mtype == "IN":
                self.increase_stock(mv.product_id, mv.quantity, mv.location_id)
            elif mtype == "OUT":
                self.decrease_stock(mv.product_id, mv.quantity, mv.location_id)

        self._save()
