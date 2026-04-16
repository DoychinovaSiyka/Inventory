from typing import List, Dict, Optional, Any
from datetime import datetime
from storage.json_repository import JSONRepository
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """Контролер за наличности по складове.
    Координира валидатор, движения и JSON хранилище. Не съдържа бизнес логика."""

    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.stock: List[Dict[str, Any]] = self.repo.load() or []

    # Помощен метод за еднакъв формат на датите
    def _get_now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Записване в JSON
    def _save(self) -> None:
        self.repo.save(self.stock)

    # Намира продукт в склад. Кастваме към str за сигурност.
    def _find(self, product_id: Any, warehouse_id: Any) -> Optional[Dict[str, Any]]:
        p_id = str(product_id)
        w_id = str(warehouse_id)
        for item in self.stock:
            if item["product_id"] == p_id and item["warehouse"] == w_id:
                return item
        return None

    def get_stock(self, product_id: Any, warehouse_id: Any) -> Optional[Dict[str, Any]]:
        return self._find(product_id, warehouse_id)

    # Параметър should_save за оптимизация при масови операции
    def increase_stock(self, product_id, product_name, warehouse_id, qty, should_save=True):
        InventoryValidator.validate_increase(product_id, product_name, warehouse_id, qty)

        record = self._find(product_id, warehouse_id)
        now = self._get_now_str()

        if record:
            record["quantity"] += float(qty)
            record["modified"] = now
        else:
            self.stock.append({"product_id": str(product_id), "product": product_name,
                               "warehouse": str(warehouse_id), "quantity": float(qty),
                               "created": now, "modified": now})
        if should_save:
            self._save()

    def decrease_stock(self, product_id, warehouse_id, qty, should_save=True):
        InventoryValidator.validate_decrease(product_id, warehouse_id, qty, self.stock)

        record = self._find(product_id, warehouse_id)
        if record:
            record["quantity"] -= float(qty)
            record["modified"] = self._get_now_str()
            # Ако количеството падне до 0 – премахваме записа
            if record["quantity"] <= 0:
                self.stock.remove(record)

        if should_save:
            self._save()

    def move_stock(self, product_id, product_name, from_wh, to_wh, qty):
        InventoryValidator.validate_move(product_id, product_name, from_wh, to_wh, qty)

        # Първо намаляваме, но не записваме – записваме само веднъж накрая
        self.decrease_stock(product_id, from_wh, qty, should_save=False)
        self.increase_stock(product_id, product_name, to_wh, qty, should_save=True)

    def get_warehouses_with_product(self, product_name: str) -> List[str]:
        search_name = product_name.lower().strip()
        return [item["warehouse"] for item in self.stock
                if item["product"].lower() == search_name and item["quantity"] > 0]

    def rebuild_from_movements(self, movements: List[Dict[str, Any]]) -> None:
        """Оптимизирано преизчисляване – записва само веднъж накрая."""
        self.stock = []
        # Сортиране по дата
        movements = sorted(movements, key=lambda m: m.get("date", ""))
        InventoryValidator.validate_movements(movements)
        for m in movements:
            pid = str(m["product_id"])
            pname = m.get("product", "N/A")
            qty = float(m["quantity"])
            mtype = m["movement_type"]
            try:
                if mtype == "IN":
                    self.increase_stock(pid, pname, m["location_id"], qty, should_save=False)
                elif mtype == "OUT":
                    self.decrease_stock(pid, m["location_id"], qty, should_save=False)
                elif mtype == "MOVE":
                    self.decrease_stock(pid, m.get("from_location_id"), qty, should_save=False)
                    self.increase_stock(pid, pname, m.get("to_location_id"), qty, should_save=False)
            except Exception:
                # Ако има грешка в движение – пропускаме го, но не спираме процеса
                continue

        self._save()

    def initialize_from_products(self, products: List[Any]) -> None:
        """Създава начални записи за наличностите на база продуктите.
        Използва се само при първоначално стартиране на системата."""
        for p in products:
            if p.location_id and p.quantity > 0:
                InventoryValidator.validate_initial_stock(p.product_id, p.name, p.location_id, p.quantity)
                self.increase_stock(product_id=p.product_id, product_name=p.name,
                                    warehouse_id=p.location_id, qty=p.quantity, should_save=False)

        self._save()
