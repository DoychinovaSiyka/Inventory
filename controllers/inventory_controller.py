from typing import Dict, Any, List
from datetime import datetime
from storage.json_repository import JSONRepository
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """Нов ERP-коректен контролер за наличности."""

    def __init__(self, repo: JSONRepository):
        self.repo = repo
        # Зареждаме данните веднъж при инициализация
        self.data: Dict[str, Any] = self.repo.load() or {"products": {}}

        # Ако структурата е стара (списък), мигрираме към речник
        if isinstance(self.data, list):
            self.data = {"products": {}}

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _save(self):
        self.repo.save(self.data)

    def _get_product(self, product_id: str) -> Dict[str, Any]:
        return self.data["products"].get(product_id)

    def _ensure_product(self, product_id: str, name: str, unit: str):
        if product_id not in self.data["products"]:
            self.data["products"][product_id] = {
                "name": name,
                "unit": unit,
                "total_stock": 0.0,
                "locations": {},
                "created": self._now(),
                "modified": self._now()
            }


    def get_warehouses_with_product(self, product_name):
        """Намира всички складове, в които даден продукт има наличност > 0."""
        warehouses_found = []
        product_name_lower = product_name.lower()

        # Използваме self.data, защото това е заредило информацията от JSON-а
        products_dict = self.data.get("products", {})

        for p_id, p_info in products_dict.items():
            if product_name_lower in p_info.get("name", "").lower():
                locations = p_info.get("locations", {})
                for loc_id, qty in locations.items():
                    if qty > 0:
                        warehouses_found.append(loc_id)

        return list(set(warehouses_found))  # Махаме дубликати, ако има такива



    def get_total_stock(self, product_id: str) -> float:
        p = self._get_product(product_id)
        return float(p["total_stock"]) if p else 0.0

    def get_stock_for_location(self, product_id: str, warehouse_id: str) -> float:
        p = self._get_product(product_id)
        if not p:
            return 0.0
        return float(p["locations"].get(warehouse_id, 0.0))

    def increase_stock(self, product_id, product_name, warehouse_id, qty, unit):
        InventoryValidator.validate_increase(product_id, product_name, warehouse_id, qty)
        self._ensure_product(product_id, product_name, unit)

        p = self._get_product(product_id)
        qty = float(qty)
        p["total_stock"] += qty
        p["locations"][warehouse_id] = p["locations"].get(warehouse_id, 0.0) + qty
        p["modified"] = self._now()
        self._save()

    def decrease_stock(self, product_id, warehouse_id, qty, unit):
        # Внимавай тук: InventoryValidator трябва да поддържа новата структура
        InventoryValidator.validate_decrease(product_id, warehouse_id, qty, self.data)

        p = self._get_product(product_id)
        if not p: return

        qty = float(qty)
        p["total_stock"] -= qty
        if warehouse_id in p["locations"]:
            p["locations"][warehouse_id] -= qty
            if p["locations"][warehouse_id] <= 0:
                del p["locations"][warehouse_id]

        p["modified"] = self._now()
        self._save()

    def move_stock(self, product_id, product_name, from_wh, to_wh, qty, unit):
        InventoryValidator.validate_move(product_id, product_name, from_wh, to_wh, qty)
        qty = float(qty)
        p = self._get_product(product_id)
        if not p: return

        if from_wh in p["locations"]:
            p["locations"][from_wh] -= qty
            if p["locations"][from_wh] <= 0:
                del p["locations"][from_wh]

        p["locations"][to_wh] = p["locations"].get(to_wh, 0.0) + qty
        p["modified"] = self._now()
        self._save()

    def initialize_from_products(self, products):
        for p in products:
            if p.quantity > 0 and p.location_id:
                self.increase_stock(
                    product_id=p.product_id,
                    product_name=p.name,
                    warehouse_id=p.location_id,
                    qty=p.quantity,
                    unit=p.unit
                )



    #  ПЪЛНО ПРЕСМЯТАНЕ НА ИНВЕНТАРА
    def rebuild_inventory_from_movements(self, movements):
        """
        Пълно пресмятане на инвентара от movements.json.
        Изтрива стария инвентар и го изгражда наново.
        """

        # 1) Изчистваме текущия инвентар
        self.data = {"products": {}}

        # 2) Обхождаме всички движения по ред
        for m in movements:

            pid = m.product_id
            pname = m.product_name
            qty = float(m.quantity)
            unit = m.unit

            # IN → добавяме в location_id
            if m.movement_type.name == "IN":
                self.increase_stock(pid, pname, m.location_id, qty, unit)

            # OUT → изваждаме от location_id
            elif m.movement_type.name == "OUT":
                self.decrease_stock(pid, m.location_id, qty, unit)

            # MOVE → местим между складове
            elif m.movement_type.name == "MOVE":
                self.move_stock(pid, pname, m.from_location_id, m.to_location_id, qty, unit)

        # 3) Записваме новия инвентар
        self._save()
