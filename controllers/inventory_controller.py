from typing import Dict, Any, List
from datetime import datetime
from storage.json_repository import JSONRepository
from validators.inventory_validator import InventoryValidator


class InventoryController:
    """ERP-коректен контролер за наличности, базиран на движенията (IN/OUT/MOVE)."""

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

    def _get_product(self, product_id: str) -> Dict[str, Any] | None:
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

    # ================== ПУБЛИЧНИ МЕТОДИ ЗА СПРАВКИ ==================

    def get_warehouses_with_product(self, product_name: str) -> List[str]:
        """Намира всички складове, в които даден продукт има наличност > 0."""
        warehouses_found: List[str] = []
        product_name_lower = product_name.lower()

        products_dict = self.data.get("products", {})

        for _, p_info in products_dict.items():
            if product_name_lower in p_info.get("name", "").lower():
                locations = p_info.get("locations", {})
                for loc_id, qty in locations.items():
                    if float(qty) > 0:
                        warehouses_found.append(loc_id)

        return list(set(warehouses_found))

    def get_total_stock(self, product_id: str) -> float:
        p = self._get_product(product_id)
        return float(p["total_stock"]) if p else 0.0

    def get_stock_for_location(self, product_id: str, warehouse_id: str) -> float:
        p = self._get_product(product_id)
        if not p:
            return 0.0
        return float(p["locations"].get(warehouse_id, 0.0))

    # ================== ОПЕРАЦИИ ВЪРХУ НАЛИЧНОСТТА ==================

    def increase_stock(self, product_id: str, product_name: str,
                       warehouse_id: str, qty: float, unit: str) -> None:
        InventoryValidator.validate_increase(product_id, product_name, warehouse_id, qty)
        self._ensure_product(product_id, product_name, unit)

        p = self._get_product(product_id)
        qty = float(qty)

        p["total_stock"] = float(p.get("total_stock", 0.0)) + qty
        p["locations"][warehouse_id] = float(p["locations"].get(warehouse_id, 0.0)) + qty
        p["modified"] = self._now()
        self._save()

    def decrease_stock(self, product_id: str, warehouse_id: str,
                       qty: float, unit: str) -> None:
        InventoryValidator.validate_decrease(product_id, warehouse_id, qty, self.data)

        p = self._get_product(product_id)
        if not p:
            return

        qty = float(qty)
        p["total_stock"] = float(p.get("total_stock", 0.0)) - qty

        if warehouse_id in p["locations"]:
            p["locations"][warehouse_id] = float(p["locations"][warehouse_id]) - qty
            if p["locations"][warehouse_id] <= 0:
                del p["locations"][warehouse_id]

        p["modified"] = self._now()
        self._save()

    def move_stock(self, product_id: str, product_name: str,
                   from_wh: str, to_wh: str, qty: float, unit: str) -> None:
        """
        MOVE: не променя total_stock, а само преразпределя между локации.
        """

        #  Подаваме master_inventory (self.data)
        InventoryValidator.validate_move(
            product_id,
            product_name,
            from_wh,
            to_wh,
            qty,
            self.data
        )

        p = self._get_product(product_id)
        if not p:
            return

        qty = float(qty)

        # Махаме от изходния склад
        if from_wh in p["locations"]:
            p["locations"][from_wh] = float(p["locations"][from_wh]) - qty
            if p["locations"][from_wh] <= 0:
                del p["locations"][from_wh]

        # Добавяме в целевия склад
        p["locations"][to_wh] = float(p["locations"].get(to_wh, 0.0)) + qty

        p["modified"] = self._now()
        self._save()

    # ================== ИНИЦИАЛИЗАЦИЯ ОТ ПРОДУКТИ ==================

    def initialize_from_products(self, products: List[Any]) -> None:
        """
        Еднократна инициализация на инвентара от каталога с продукти.
        quantity тук се третира като „начална наличност“.
        Ако продуктът няма location_id, по подразбиране се слага в W1.
        """
        for p in products:
            # quantity > 0 → има начална наличност
            if getattr(p, "quantity", 0) and float(p.quantity) > 0:
                warehouse_id = getattr(p, "location_id", None) or "W1"
                self.increase_stock(
                    product_id=p.product_id,
                    product_name=p.name,
                    warehouse_id=warehouse_id,
                    qty=p.quantity,
                    unit=p.unit
                )

    # ================== ПЪЛНО ПРЕСМЯТАНЕ ОТ movements.json ==================

    def rebuild_inventory_from_movements(self, movements: List[Any]) -> None:
        """
        Пълно пресмятане на инвентара от movements.json.
        Изтрива стария инвентар и го изгражда наново само на база движенията.
        Това е ERP-коректният източник на истина.
        """

        # 1) Изчистваме текущия инвентар
        self.data = {"products": {}}

        # 2) Обхождаме всички движения по ред
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

        # 3) Записваме новия инвентар
        self._save()
