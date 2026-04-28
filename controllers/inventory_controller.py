from typing import Dict, Any, List
from datetime import datetime
from storage.json_repository import JSONRepository
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """Контролерът управлява наличностите. Работи коректно дори когато JSON файловете са празни."""
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        data = self.repo.load()

        if not data or not isinstance(data, dict):
            self.data = {"products": {}}
            return

        if isinstance(data, list):
            self.data = {"products": {}}
            return

        if "products" not in data:
            data["products"] = {}

        self.data = data

    def _save(self):
        self.repo.save(self.data)

    def _get_product(self, product_id: str) -> Dict[str, Any] | None:
        return self.data["products"].get(product_id)

    def _ensure_product(self, product_id: str, name: str, unit: str):
        if product_id not in self.data["products"]:
            self.data["products"][product_id] = {"name": name,
                                                 "unit": unit,
                                                 "total_stock": 0.0, "locations": {}}

    # СПРАВКИ
    def get_warehouses_with_product(self, product_name: str) -> List[str]:
        warehouses = []
        name_lower = product_name.lower()

        for p_info in self.data["products"].values():
            if name_lower in p_info.get("name", "").lower():
                for loc_id, qty in p_info.get("locations", {}).items():
                    if float(qty) > 0:
                        warehouses.append(loc_id)

        return list(set(warehouses))

    def get_total_stock(self, product_id: str) -> float:
        p = self._get_product(product_id)
        if not p:
            return 0.0
        return float(p.get("total_stock", 0.0))

    def get_stock_for_location(self, product_id: str, warehouse_id: str) -> float:
        p = self._get_product(product_id)
        if not p:
            return 0.0
        return float(p["locations"].get(warehouse_id, 0.0))

    # ОПЕРАЦИИ
    def increase_stock(self, product_id: str, product_name: str, warehouse_id: str,
                       qty: float, unit: str) -> None:

        if qty <= 0:
            return

        self._ensure_product(product_id, product_name, unit)

        p = self._get_product(product_id)
        qty = float(qty)

        p["total_stock"] = float(p.get("total_stock", 0.0)) + qty
        p["locations"][warehouse_id] = float(p["locations"].get(warehouse_id, 0.0)) + qty

        self._save()

    def decrease_stock(self, product_id: str, warehouse_id: str, qty: float, unit: str) -> None:
        if qty <= 0:
            return

        p = self._get_product(product_id)
        if not p:
            return

        qty = float(qty)
        current = float(p.get("total_stock", 0.0))

        if current < qty:
            return

        p["total_stock"] = current - qty

        if warehouse_id in p["locations"]:
            new_qty = float(p["locations"][warehouse_id]) - qty
            if new_qty > 0:
                p["locations"][warehouse_id] = new_qty
            else:
                del p["locations"][warehouse_id]

        self._save()   # ← ЛИПСВАШЕ

    def move_stock(self, product_id: str, product_name: str, from_wh: str,
                   to_wh: str, qty: float, unit: str) -> None:

        if qty <= 0:
            return

        p = self._get_product(product_id)
        if not p:
            return

        qty = float(qty)

        if from_wh not in p["locations"]:
            return

        new_qty = float(p["locations"][from_wh]) - qty
        if new_qty > 0:
            p["locations"][from_wh] = new_qty
        else:
            del p["locations"][from_wh]

        p["locations"][to_wh] = float(p["locations"].get(to_wh, 0.0)) + qty

        self._save()

    # ПЪЛНО ПРЕСМЯТАНЕ
    def rebuild_inventory_from_movements(self, movements: List[Any]) -> None:
        self.data = {"products": {}}

        if not movements:
            self._save()
            return

        for m in movements:
            pid = m.product_id
            pname = m.product_name
            qty = float(m.quantity)
            unit = m.unit

            if m.movement_type.name == "IN":
                self.increase_stock(pid, pname, m.location_id, qty, unit)

            elif m.movement_type.name == "OUT":
                self.decrease_stock(pid, m.location_id, qty, unit)

            elif m.movement_type.name == "MOVE":
                self.move_stock(pid, pname, m.from_location_id, m.to_location_id, qty, unit)

        self._save()
