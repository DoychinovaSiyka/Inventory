import uuid
from typing import Optional, List
from datetime import datetime

from storage.json_repository import Repository
from models.product import Product
from validators.product_validator import ProductValidator
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController

from filters.product_filters import (filter_search, filter_by_multiple_category_ids,
                                     filter_by_category, filter_by_supplier, filter_by_price_range,
                                     filter_by_quantity_range, filter_low_stock, filter_warehouses, filter_combined)


class ProductController:
    def __init__(self, repo: Repository, category_controller: CategoryController,
                 supplier_controller: SupplierController, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.supplier_controller = supplier_controller
        self.activity_log = activity_log_controller

        self.products: List[Product] = []
        self._load_products()

    #  INTERNAL HELPERS
    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    def _validate_supplier(self, supplier_id):
        if supplier_id is not None:
            if not self.supplier_controller.get_by_id(supplier_id):
                raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")

    def _validate_categories(self, category_ids):
        categories = []
        for cid in category_ids:
            c = self.category_controller.get_by_id(cid)
            if not c:
                raise ValueError(f"Категория с ID {cid} не съществува.")
            categories.append(c)
        return categories

    def _log(self, user_id, action, message):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    def _load_products(self):
        for p_data in self.repo.load():
            product = Product.from_dict(p_data)

            fixed_categories = []
            for cid in product.categories:
                if isinstance(cid, str):
                    c = self.category_controller.get_by_id(cid)
                else:
                    c_id = getattr(cid, 'category_id', cid)
                    c = self.category_controller.get_by_id(c_id)
                if c:
                    fixed_categories.append(c)

            product.categories = fixed_categories
            self.products.append(product)

    # CREATE PRODUCT
    def add(self, name: str, category_ids: List[str], quantity: float, unit: str,
            description: str, price: float, supplier_id: Optional[str], user_id: str,
            location_id: str = "W1", tags: Optional[List[str]] = None) -> Product:

        ProductValidator.validate_all(name, category_ids, quantity, unit, description, price)
        if any(p.name.lower() == name.lower() and p.location_id == location_id
               for p in self.products):
            raise ValueError(f"Продукт с име '{name}' вече съществува в склад {location_id}.")

        categories = self._validate_categories(category_ids)
        self._validate_supplier(supplier_id)

        now = str(datetime.now())

        product = Product(product_id=self._generate_id(),
            name=name, categories=categories, quantity=float(quantity), unit=unit,
            description=description, price=price, supplier_id=supplier_id, location_id=location_id,
            tags=tags or [], created=now, modified=now)

        self.products.append(product)
        self.save_changes()
        self._log(user_id, "ADD_PRODUCT", f"Added product: {product.name}")

        return product

    #  READ
    def get_all(self) -> List[Product]:
        return self.products

    def get_by_id(self, product_id: str) -> Optional[Product]:
        return next((p for p in self.products if str(p.product_id) == str(product_id)), None)

    def exists_by_name(self, name: str) -> bool:
        return any(p.name.lower() == name.lower() for p in self.products)

    # UPDATE
    def update_name(self, product_id: str, new_name: str, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        if self.exists_by_name(new_name) and new_name != p.name:
            raise ValueError("Продукт с това име вече съществува.")

        ProductValidator.validate_name(new_name)
        p.name = new_name
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated name of product ID {product_id} to '{new_name}'")
        return True

    def update_description(self, product_id: str, new_description: str, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        ProductValidator.validate_description(new_description)
        p.description = new_description
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated description of product ID {product_id}")
        return True

    def update_categories(self, product_id: str, new_category_ids: List[str], user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        categories = self._validate_categories(new_category_ids)
        p.categories = categories
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated categories of product ID {product_id}")
        return True

    def update_supplier(self, product_id: str, supplier_id: str, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        self._validate_supplier(supplier_id)
        p.supplier_id = supplier_id
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated supplier of product ID {product_id}")
        return True

    def update_price(self, product_id: str, new_price: float, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")

        ProductValidator.validate_price(new_price)
        p.price = round(float(new_price), 2)
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated price of product ID {product_id} to {new_price}")
        return True

    #  QUANTITY
    def increase_quantity(self, product_id: str, amount: float, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")
        if amount < 0:
            raise ValueError("Количество трябва да е положително.")

        p.quantity = round(p.quantity + float(amount), 2)
        p.update_modified()
        self.save_changes()
        self._log(user_id, "INCREASE_QUANTITY", f"Added {amount} units to product ID {product_id}")
        return True

    def decrease_quantity(self, product_id: str, amount: float, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if not p:
            raise ValueError("Продуктът не е намерен.")
        if amount < 0:
            raise ValueError("Количество трябва да е положително.")
        if p.quantity < amount:
            raise ValueError("Недостатъчна наличност.")

        p.quantity = round(p.quantity - float(amount), 2)
        p.update_modified()
        self.save_changes()
        self._log(user_id, "DECREASE_QUANTITY", f"Removed {amount} units from product ID {product_id}")
        return True

    # DELETE
    def remove_by_id(self, product_id: str, user_id: str) -> bool:
        original_len = len(self.products)
        self.products = [p for p in self.products if str(p.product_id) != str(product_id)]

        if len(self.products) < original_len:
            self.save_changes()
            self._log(user_id, "DELETE_PRODUCT", f"Deleted product ID {product_id}")
            return True
        return False

    def remove_by_name(self, name: str, user_id: str) -> bool:
        name = name.lower()
        original_len = len(self.products)
        self.products = [p for p in self.products if p.name.lower() != name]

        if len(self.products) < original_len:
            self.save_changes()
            self._log(user_id, "DELETE_PRODUCT", f"Deleted product '{name}'")
            return True
        return False

    #  FILTERS (вече използват product_filters.py)
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

    #  STATISTICS
    def average_price(self) -> float:
        if not self.products:
            return 0.0
        return sum(p.price for p in self.products) / len(self.products)

    def total_values(self) -> float:
        return round(sum(p.price * p.quantity for p in self.products), 2)

    def most_expensive(self) -> Optional[Product]:
        return max(self.products, key=lambda p: p.price, default=None)

    def cheapest(self) -> Optional[Product]:
        return min(self.products, key=lambda p: p.price, default=None)

    def group_by_category(self) -> dict:
        grouped = {}
        for p in self.products:
            for c in p.categories:
                c_id = getattr(c, 'category_id', c)
                grouped.setdefault(c_id, []).append(p)
        return grouped

    # SORTING
    def sort_by_name(self) -> List[Product]:
        self.products.sort(key=lambda p: p.name.lower())
        return self.products

    def sort_by_price_desc(self) -> List[Product]:
        return sorted(self.products, key=lambda p: p.price, reverse=True)

    def bubble_sort(self, key=lambda p: p.price, reverse=True) -> List[Product]:
        sorted_products = self.products[:]
        n = len(sorted_products)
        for i in range(n):
            for j in range(0, n - i - 1):
                a = key(sorted_products[j])
                b = key(sorted_products[j + 1])

                if reverse and a < b:
                    sorted_products[j], sorted_products[j + 1] = sorted_products[j + 1], sorted_products[j]
                elif not reverse and a > b:
                    sorted_products[j], sorted_products[j + 1] = sorted_products[j + 1], sorted_products[j]

        return sorted_products

    def selection_sort(self, key=lambda p: p.price, reverse=True) -> List[Product]:
        sorted_products = self.products[:]
        n = len(sorted_products)
        for i in range(n):
            best_idx = i
            for j in range(i + 1, n):
                a = key(sorted_products[j])
                b = key(sorted_products[best_idx])

                if reverse and a > b:
                    best_idx = j
                elif not reverse and a < b:
                    best_idx = j

            sorted_products[i], sorted_products[best_idx] = sorted_products[best_idx], sorted_products[i]

        return sorted_products

    #  SAVE
    def save_changes(self) -> None:
        self.repo.save([p.to_dict() for p in self.products])
