from typing import List, Dict
from datetime import datetime
from storage.json_repository import JSONRepository
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """ Управлява наличностите по складове. Работи автоматично с IN / OUT / MOVE движения.
    Данните се пазят в inventory.json."""

    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.stock: List[Dict] = self.repo.load() or []

    def save(self):
        self.repo.save(self.stock)

    def _find(self, product_id, warehouse_id):
        for item in self.stock:
            if item["product_id"] == product_id and item["warehouse"] == warehouse_id:
                return item
        return None

    #  ПУБЛИЧЕН МЕТОД – използва се от MovementController
    def get_stock(self, product_id, warehouse_id):
        return self._find(product_id, warehouse_id)

    # Създаване на продукт
    def create_initial_stock(self, product_id, product_name, warehouse_id, qty):
        InventoryValidator.validate_initial_stock(product_id, product_name, warehouse_id, qty)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.stock.append({
            "product_id": product_id,
            "product": product_name,
            "warehouse": warehouse_id,
            "quantity": qty,
            "created": now,
            "modified": now
        })
        self.save()

    # IN движение
    def increase_stock(self, product_id, product_name, warehouse_id, qty):
        InventoryValidator.validate_increase(product_id, product_name, warehouse_id, qty)

        record = self._find(product_id, warehouse_id)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        self.save()

    # OUT движение
    def decrease_stock(self, product_id, warehouse_id, qty):
        InventoryValidator.validate_decrease(product_id, warehouse_id, qty, self.stock)

        record = self._find(product_id, warehouse_id)
        record["quantity"] -= qty
        record["modified"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if record["quantity"] == 0:
            self.stock.remove(record)

        self.save()

    # MOVE движение
    def move_stock(self, product_id, product_name, from_wh, to_wh, qty):
        InventoryValidator.validate_move(product_id, product_name, from_wh, to_wh, qty)
        self.decrease_stock(product_id, from_wh, qty)
        self.increase_stock(product_id, product_name, to_wh, qty)

    # За Dijkstra – търсим по ИМЕ на продукт
    def get_warehouses_with_product(self, product_name):
        result = []
        for item in self.stock:
            if item["product"].lower() == product_name.lower() and item["quantity"] > 0:
                result.append(item["warehouse"])
        return result

    # Преизчислява инвентара от списък с движения
    def rebuild_from_movements(self, movements):
        self.stock = []  # изчистваме текущия инвентар

        movements = sorted(movements, key=lambda m: m["date"])
        InventoryValidator.validate_movements(movements)

        for m in movements:
            pid = m["product_id"]
            pname = m.get("product", "")
            qty = float(m["quantity"])
            mtype = m["movement_type"]
            loc = m["location_id"]
            from_loc = m.get("from_location_id")
            to_loc = m.get("to_location_id")

            if mtype == "IN":
                self.increase_stock(pid, pname, loc, qty)
            elif mtype == "OUT":
                try:
                    self.decrease_stock(pid, loc, qty)
                except:
                    pass
            elif mtype == "MOVE":
                try:
                    self.decrease_stock(pid, from_loc, qty)
                except:
                    pass
                self.increase_stock(pid, pname, to_loc, qty)

        self.save()
