import uuid
from typing import Optional, List
from datetime import datetime
from models.product import Product
from validators.product_validator import ProductValidator
from filters.product_filters import (filter_search, filter_by_multiple_category_ids,
                                     filter_by_category, filter_by_supplier,
                                     filter_by_price_range, filter_low_stock,
                                     filter_warehouses, filter_combined)

from sorting.product_sorters import (sort_by_name_logic, sort_by_price_desc_logic,
                                     bubble_sort_logic, selection_sort_logic)

from analytics.product_analytics import (calculate_average_price, calculate_total_inventory_value,
                                         get_most_expensive_product, get_cheapest_product,
                                         group_products_by_category)


class ProductController:
    """Контролерът отговаря за работа с продуктите. Оправен за оптимизиран запис."""

    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.activity_log = activity_log_controller

        self.products: List[Product] = []
        self._load_products()

        self.supplier_controller = None
        self.inventory_controller = None
        self.movement_controller = None

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _log(self, user_id, action, message):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    def _load_products(self):
        raw = self.repo.load() or []
        self.products = [Product.from_dict(p_data, self.category_controller)
                         for p_data in raw]

    def get_all(self) -> List[Product]:
        return self.products

    def get_by_id(self, product_id: str) -> Optional[Product]:
        return next((p for p in self.products if str(p.product_id) == str(product_id)), None)

    def save_changes(self) -> None:
        """Записва промените само когато е извикано експлицитно."""
        data_to_save = [p.to_dict() for p in self.products]
        self.repo.save(data_to_save)

    def add(self, product_data: dict, user_id: str) -> Product:
        """Добавя нов продукт и прави начално IN движение."""
        ProductValidator.validate_category_exists(product_data['category_ids'], self.category_controller)
        ProductValidator.validate_name(product_data['name'])

        now = self._now()
        categories = [self.category_controller.get_by_id(cid) for cid in product_data['category_ids']]

        product = Product(product_id=self._generate_id(), name=product_data['name'],
                          categories=categories, unit=product_data['unit'],
                          description=product_data['description'], price=float(product_data['price']),
                          supplier_id=product_data.get('supplier_id'), tags=product_data.get('tags', []),
                          location_id=product_data.get('location_id'), created=now, modified=now)

        self.products.append(product)

        # Записваме новия продукт
        self.save_changes()
        self._log(user_id, "ADD_PRODUCT", f"Добавен продукт: {product.name}")

        # Начално количество чрез движение (това ще направи запис в movements.json)
        quantity = product_data.get("quantity")
        location_id = product_data.get("location_id") or "W1"

        if quantity and self.movement_controller:
            qty = float(quantity)
            if qty > 0:
                self.movement_controller.add(product_id=product.product_id, user_id=user_id,
                                             location_id=location_id, movement_type="IN", quantity=str(qty),
                                             description="Начално зареждане при създаване", rice=str(product.price),
                                             supplier_id=product.supplier_id or "system")
        return product

    def update_product(self, product_id: str, new_name: Optional[str], new_description: Optional[str],
                       new_price: float, new_quantity: Optional[float] = None, new_unit: Optional[str] = None,
                       new_category_ids: Optional[List[str]] = None, new_location_id: Optional[str] = None,
                       new_supplier_id: Optional[str] = None, new_tags: Optional[List[str]] = None,
                       user_id: str = "system") -> bool:

        product = ProductValidator.validate_product_exists(product_id, self)
        has_changes = False

        if new_name and new_name.lower() != product.name.lower():
            ProductValidator.validate_name(new_name)
            product.name = new_name
            has_changes = True

        if new_price and float(new_price) != product.price:
            product.price = ProductValidator.validate_price(new_price)
            has_changes = True

        if new_quantity is not None and self.inventory_controller and self.movement_controller:
            current_stock = self.inventory_controller.get_total_stock(product_id)
            diff = float(new_quantity) - float(current_stock)

            if abs(diff) > 0.001:
                m_type = "IN" if diff > 0 else "OUT"
                self.movement_controller.add(product_id=product_id, user_id=user_id,
                                             location_id=new_location_id or product.location_id or "W1",
                                             movement_type=m_type, quantity=str(abs(diff)),
                                             description=f"Корекция ({m_type}) от редакция", price=str(product.price),
                                             supplier_id=product.supplier_id or "system")

        if new_category_ids:
            product.categories = [self.category_controller.get_by_id(cid) for cid in new_category_ids]
            has_changes = True

        if has_changes:
            product.update_modified()
            self.save_changes()
            self._log(user_id, "EDIT_PRODUCT", f"Обновен продукт: {product.name}")

        return True

    def delete_by_id(self, product_id: str, user_id: str) -> bool:
        product = self.get_by_id(product_id)
        if product:
            self.products = [p for p in self.products if str(p.product_id) != str(product_id)]
            self.save_changes()
            self._log(user_id, "DELETE_PRODUCT", f"Изтрит продукт ID {product_id}")
            return True
        return False

    # Справки и филтри
    def search(self, keyword: str) -> List[Product]:
        return filter_search(self.products, keyword)

    def check_low_stock(self, threshold: float = 5) -> List[Product]:
        return filter_low_stock(self.products, threshold, self.inventory_controller)

    def total_values(self) -> float:
        return calculate_total_inventory_value(self.products, self.inventory_controller)