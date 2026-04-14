from typing import List, Dict, Optional
from datetime import datetime
from storage.json_repository import JSONRepository
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """ Управлява наличностите по складове. """
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.stock: List[Dict] = self.repo.load() or []

    def _get_now_str(self) -> str:
        """ Помощен метод за еднакъв формат на датите. """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def save(self):
        self.repo.save(self.stock)

    def _find(self, product_id, warehouse_id) -> Optional[Dict]:
        """ Намира продукт в склад. Кастваме към str за сигурност. """
        p_id = str(product_id)
        w_id = str(warehouse_id)
        for item in self.stock:
            if str(item["product_id"]) == p_id and str(item["warehouse"]) == w_id:
                return item
        return None

    def get_stock(self, product_id, warehouse_id):
        return self._find(product_id, warehouse_id)

    # Добавен параметър should_save, за да оптимизираме масовите операции
    def increase_stock(self, product_id, product_name, warehouse_id, qty, should_save=True):
        InventoryValidator.validate_increase(product_id, product_name, warehouse_id, qty)

        record = self._find(product_id, warehouse_id)
        now = self._get_now_str()

        if record:
            record["quantity"] += qty
            record["modified"] = now
        else:
            self.stock.append({
                "product_id": product_id,
                "product": product_name,
                "warehouse": warehouse_id,
                "quantity": qty,
                "created": now,
                "modified": now
            })

        if should_save:
            self.save()

    def decrease_stock(self, product_id, warehouse_id, qty, should_save=True):
        InventoryValidator.validate_decrease(product_id, warehouse_id, qty, self.stock)

        record = self._find(product_id, warehouse_id)
        if record:
            record["quantity"] -= qty
            record["modified"] = self._get_now_str()

            if record["quantity"] <= 0:
                self.stock.remove(record)

        if should_save:
            self.save()

    def move_stock(self, product_id, product_name, from_wh, to_wh, qty):
        InventoryValidator.validate_move(product_id, product_name, from_wh, to_wh, qty)
        # Тук използваме should_save=False за първата стъпка, за да запишем само веднъж
        self.decrease_stock(product_id, from_wh, qty, should_save=False)
        self.increase_stock(product_id, product_name, to_wh, qty, should_save=True)

    def get_warehouses_with_product(self, product_name):
        search_name = product_name.lower().strip()
        return [item["warehouse"] for item in self.stock
                if item["product"].lower() == search_name and item["quantity"] > 0]

    def rebuild_from_movements(self, movements):
        """ Оптимизирано преизчисляване - записва само веднъж накрая! """
        self.stock = []

        # Сортиране по дата
        movements = sorted(movements, key=lambda m: m.get("date", ""))
        InventoryValidator.validate_movements(movements)

        for m in movements:
            pid = m["product_id"]
            pname = m.get("product", "N/A")
            qty = float(m["quantity"])
            mtype = m["movement_type"]

            if mtype == "IN":
                self.increase_stock(pid, pname, m["location_id"], qty, should_save=False)
            elif mtype == "OUT":
                try:
                    self.decrease_stock(pid, m["location_id"], qty, should_save=False)
                except:
                    pass
            elif mtype == "MOVE":
                try:
                    self.decrease_stock(pid, m.get("from_location_id"), qty, should_save=False)
                    self.increase_stock(pid, pname, m.get("to_location_id"), qty, should_save=False)
                except:
                    pass

        self.save()  # Записваме финалния резултат веднъж