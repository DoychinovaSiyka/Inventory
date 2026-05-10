from typing import List, Dict, Optional


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

    def _resolve_ids(self, product_id: str, location_id: Optional[str] = None):
        """ превръщане на частични/потребителски ID-та в пълни системни UUID-та."""
        prod = self.product_controller.get_by_id(str(product_id))
        full_pid = prod.product_id if prod else str(product_id)

        full_lid = None
        if location_id:
            loc = self.location_controller.get_by_id(str(location_id))
            full_lid = loc.location_id if loc else str(location_id)

        return full_pid, full_lid


    def get_stock(self, product_id: str, location_id: str) -> float:
        """Връща наличността на продукт в конкретен склад."""
        pid, lid = self._resolve_ids(product_id, location_id)
        if not lid or pid not in self.data["products"]:
            return 0.0

        locs = self.data["products"][pid].get("locations", {})
        return float(locs.get(lid, 0.0))


    def get_total_stock(self, product_id: str) -> float:
        """Общо количество от продукта във всички складове."""
        pid, _ = self._resolve_ids(product_id)

        if pid not in self.data["products"]:
            return 0.0

        locs = self.data["products"][pid].get("locations", {})
        return sum(float(q) for q in locs.values())


    def increase_stock(self, product_id: str, quantity: float, location_id: str) -> None:
        """Увеличава наличността (при доставка или входящ трансфер)."""
        pid, lid = self._resolve_ids(product_id, location_id)
        if not lid: return

        if pid not in self.data["products"]:
            self.data["products"][pid] = {"locations": {}}

        locs = self.data["products"][pid]["locations"]
        locs[lid] = round(float(locs.get(lid, 0.0)) + float(quantity), 2)
        self._save()

    def decrease_stock(self, product_id: str, quantity: float, location_id: str) -> bool:
        pid, lid = self._resolve_ids(product_id, location_id)

        if not lid or pid not in self.data["products"]:
            return False

        locs = self.data["products"][pid]["locations"]
        current = float(locs.get(lid, 0.0))
        qty_to_remove = float(quantity)

        if current < qty_to_remove:
            return False

        locs[lid] = round(current - qty_to_remove, 2)
        self._save()
        return True



    def rebuild_inventory_from_movements(self, movements: List) -> None:
        """Пълна ревизия: Преизчислява целия инвентар от историята на движенията."""
        self.data = {"products": {}}
        # Важно е движенията да са хронологично подредени
        sorted_moves = sorted(movements, key=lambda m: m.date)

        for m in sorted_moves:
            pid = str(m.product_id)
            qty = float(m.quantity)
            m_type = m.movement_type.name if hasattr(m.movement_type, "name") else str(m.movement_type)

            if pid not in self.data["products"]:
                self.data["products"][pid] = {"locations": {}}

            locs = self.data["products"][pid]["locations"]

            if m_type == "IN" and m.location_id:
                locs[m.location_id] = locs.get(m.location_id, 0.0) + qty
            elif m_type == "OUT" and m.location_id:
                locs[m.location_id] = max(0.0, locs.get(m.location_id, 0.0) - qty)
            elif m_type == "MOVE":
                if m.from_location_id:
                    locs[m.from_location_id] = max(0.0, locs.get(m.from_location_id, 0.0) - qty)
                if m.to_location_id:
                    locs[m.to_location_id] = locs.get(m.to_location_id, 0.0) + qty

        self._save()



    def calculate_fifo_cost(self, product_id: str, movements: List, fallback_price: float = 0.0) -> float:
        """Пресмята себестойността на продадените количества по метода FIFO."""
        pid, _ = self._resolve_ids(product_id)

        # Намираме общото продадено количество
        total_sold = sum(float(m.quantity) for m in movements
                         if str(m.product_id) == pid and
                         (m.movement_type.name if hasattr(m.movement_type, "name") else str(m.movement_type)) == "OUT")

        if total_sold <= 0: return 0.0

        # Събираме всички входящи партиди (доставки)
        batches = []
        for m in sorted(movements, key=lambda x: x.date):
            m_type = m.movement_type.name if hasattr(m.movement_type, "name") else str(m.movement_type)
            if str(m.product_id) == pid and m_type == "IN":
                price = float(m.price) if (m.price and float(m.price) > 0) else float(fallback_price)
                batches.append({"qty": float(m.quantity), "price": price})

        # Разпределяме продажбите по партидите
        total_cost = 0.0
        remaining_to_calculate = total_sold
        for batch in batches:
            if remaining_to_calculate <= 0: break

            take = min(batch["qty"], remaining_to_calculate)
            total_cost += take * batch["price"]
            remaining_to_calculate -= take

        # Ако сме продали повече, отколкото сме заприходили
        if remaining_to_calculate > 0:
            total_cost += remaining_to_calculate * fallback_price

        return round(total_cost, 2)



    def get_total_inventory_value_fifo(self, movement_controller) -> float:
        """Изчислява финансовата стойност на текущия остатък в склада по FIFO."""
        total_value = 0.0
        all_moves = movement_controller.get_all()

        for pid in self.data.get("products", {}):
            product_obj = self.product_controller.get_by_id(pid)
            fb_price = float(product_obj.price) if product_obj else 0.0

            # Филтрираме движенията само за този продукт
            prod_moves = sorted([m for m in all_moves if str(m.product_id) == pid], key=lambda x: x.date)

            batches = []
            for m in prod_moves:
                m_type = m.movement_type.name if hasattr(m.movement_type, "name") else str(m.movement_type)
                qty = float(m.quantity)

                if m_type == "IN":
                    price = float(m.price) if (m.price and float(m.price) > 0) else fb_price
                    batches.append({"qty": qty, "price": price})
                elif m_type == "OUT":
                    # Консумираме от най-старите партиди
                    while qty > 0 and batches:
                        if batches[0]["qty"] <= qty:
                            qty -= batches[0].pop("qty")
                            batches.pop(0)
                        else:
                            batches[0]["qty"] -= qty
                            qty = 0

            # Стойността на това, което е останало в batches
            total_value += sum(b["qty"] * b["price"] for b in batches)

        return round(total_value, 2)