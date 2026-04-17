import uuid
from typing import Optional, List
from datetime import datetime

from models.product import Product
from validators.product_validator import ProductValidator
from filters.product_filters import (
    filter_search, filter_by_multiple_category_ids, filter_by_category,
    filter_by_supplier, filter_by_price_range, filter_by_quantity_range,
    filter_low_stock, filter_warehouses, filter_combined
)

from sorting.product_sorters import (
    sort_by_name_logic, sort_by_price_desc_logic,
    bubble_sort_logic, selection_sort_logic
)

from analytics.product_analytics import (
    calculate_average_price, calculate_total_inventory_value,
    get_most_expensive_product, get_cheapest_product,
    group_products_by_category
)

from view_models.product_view_model import ProductViewModel


class ProductController:
    """Контролерът управлява продуктите в системата."""

    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.activity_log = activity_log_controller

        self.products: List[Product] = []
        self._load_products()

        # Закачат се отвън
        self.supplier_controller = None
        self.inventory_controller = None

    # ================= INTERNAL HELPERS =================

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat()

    def _log(self, user_id, action, message):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    def _load_products(self):
        raw = self.repo.load()
        self.products = [
            Product.from_dict(p_data, self.category_controller)
            for p_data in raw
        ]

    # ================= READ =================

    def get_all(self) -> List[Product]:
        return self.products

    def get_by_id(self, product_id: str) -> Optional[Product]:
        return next((p for p in self.products if str(p.product_id) == str(product_id)), None)

    def get_by_name(self, name: str) -> Optional[Product]:
        name = name.strip().lower()
        return next((p for p in self.products if p.name.lower() == name), None)

    def exists_by_name(self, name: str) -> bool:
        return any(p.name.lower() == name.lower() for p in self.products)

    # ================= CREATE =================

    def add(self, product_data: dict, user_id: str) -> Product:
        """
        Добавя нов продукт.
        quantity се използва само за първоначално зареждане → автоматично IN движение.
        """

        # 1) Валидации
        ProductValidator.validate_all(
            product_id=None,
            name=product_data['name'],
            categories=product_data['category_ids'],
            quantity=product_data['quantity'],
            unit=product_data['unit'],
            description=product_data['description'],
            price=product_data['price'],
            location_id=product_data.get('location_id'),
            supplier_id=product_data.get('supplier_id'),
            tags=product_data.get('tags', [])
        )

        ProductValidator.validate_category_exists(product_data['category_ids'], self.category_controller)
        ProductValidator.validate_supplier_exists(product_data.get('supplier_id'), self.supplier_controller)
        ProductValidator.validate_unique_name_in_location(
            product_data['name'],
            product_data.get('location_id', 'W1'),
            self.products
        )

        # 2) Създаване на продукт
        now = self._now()
        categories = [self.category_controller.get_by_id(cid) for cid in product_data['category_ids']]

        product = Product(
            product_id=self._generate_id(),
            name=product_data['name'],
            categories=categories,
            quantity=float(product_data['quantity']),  # само за initialize_from_products
            unit=product_data['unit'],
            description=product_data['description'],
            price=float(product_data['price']),
            supplier_id=product_data.get('supplier_id'),
            location_id=product_data.get('location_id', 'W1'),
            tags=product_data.get('tags', []),
            created=now,
            modified=now
        )

        self.products.append(product)
        self.save_changes()

        # 3) Автоматично начално зареждане в инвентара
        initial_qty = float(product_data['quantity'])
        location_id = product_data.get('location_id', 'W1')

        if self.inventory_controller and initial_qty > 0:
            self.inventory_controller.increase_stock(
                product_id=product.product_id,
                product_name=product.name,
                warehouse_id=location_id,
                qty=initial_qty,
                unit=product.unit
            )

        # 4) Лог
        self._log(user_id, "ADD_PRODUCT", f"Успешно добавен: {product.name}")

        return product

    # ================= UPDATE =================

    def update_product(self, product_id: str, new_name: str,
                       new_description: str, new_price: float,
                       user_id: str = "system") -> bool:

        product = ProductValidator.validate_product_exists(product_id, self)

        if new_name and new_name.lower() != product.name.lower():
            ProductValidator.validate_name(new_name)
            ProductValidator.validate_unique_name_in_location(new_name, product.location_id, self.products)
            product.name = new_name

        if new_description and new_description != product.description:
            product.description = ProductValidator.validate_description(new_description)

        product.price = ProductValidator.validate_price(new_price)
        product.update_modified()

        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Обновен продукт: {product.name} (ID: {product_id})")
        return True

    # ================= DELETE =================

    def delete_by_id(self, product_id: str, user_id: str) -> bool:
        ProductValidator.validate_product_exists(product_id, self)

        before = len(self.products)
        self.products = [p for p in self.products if str(p.product_id) != str(product_id)]

        if len(self.products) < before:
            self.save_changes()
            self._log(user_id, "DELETE_PRODUCT", f"Изтрит продукт ID {product_id}")
            return True

        return False

    def remove_by_name(self, name: str, user_id: str) -> bool:
        name = name.lower()
        before = len(self.products)

        self.products = [p for p in self.products if p.name.lower() != name]

        if len(self.products) < before:
            self.save_changes()
            self._log(user_id, "DELETE_PRODUCT", f"Изтрит продукт '{name}'")
            return True

        return False

    # ================= INVENTORY =================

    def get_total_stock(self, product_id: str) -> float:
        if not self.inventory_controller:
            return 0.0
        return self.inventory_controller.get_total_stock(product_id)

    # ================= FILTERS =================

    def search(self, keyword: str) -> List[Product]:
        return filter_search(self.products, keyword)

    def filter_by_multiple_category_ids(self, category_ids: List[str]) -> List[Product]:
        return filter_by_multiple_category_ids(self.products, category_ids)

    def check_low_stock(self, threshold: float = 5) -> List[Product]:
        return filter_low_stock(self.products, threshold)

    def search_by_price_range(self, min_price=None, max_price=None):
        return filter_by_price_range(self.products, min_price, max_price)

    def search_by_quantity_range(self, min_qty=None, max_qty=None):
        return filter_by_quantity_range(self.products, min_qty, max_qty)

    def search_by_category(self, category_id: str):
        return filter_by_category(self.products, category_id)

    def search_by_supplier(self, supplier_id: str):
        return filter_by_supplier(self.products, supplier_id)

    def search_combined(self, *args, **kwargs):
        return filter_combined(self.products, *args, **kwargs)

    def get_warehouses_with_product(self, product_name: str):
        return filter_warehouses(self.products, product_name)

    # ================= ANALYTICS =================

    def average_price(self) -> float:
        return calculate_average_price(self.products)

    def total_values(self) -> float:
        return calculate_total_inventory_value(self.products)

    def most_expensive(self) -> Optional[Product]:
        return get_most_expensive_product(self.products)

    def cheapest(self) -> Optional[Product]:
        return get_cheapest_product(self.products)

    def group_by_category(self) -> dict:
        return group_products_by_category(self.products)

    # ================= SORTING =================

    def sort_by_name(self) -> List[Product]:
        return sort_by_name_logic(self.products)

    def sort_by_price_desc(self) -> List[Product]:
        return sort_by_price_desc_logic(self.products)

    def bubble_sort(self, key=lambda p: p.price, reverse=True) -> List[Product]:
        return bubble_sort_logic(self.products, key, reverse)

    def selection_sort(self, key=lambda p: p.price, reverse=True) -> List[Product]:
        return selection_sort_logic(self.products, key, reverse)

    # ================= SAVE =================

    def save_changes(self) -> None:
        self.repo.save([p.to_dict() for p in self.products])
