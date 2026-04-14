import uuid
from typing import Optional, List
from datetime import datetime
from storage.json_repository import Repository
from models.product import Product
from validators.product_validator import ProductValidator
from controllers.category_controller import CategoryController
from controllers.supplier_controller import SupplierController

# Филтри – изнесени в отделен пакет
from filters.product_filters import (
    filter_search, filter_by_multiple_category_ids, filter_by_category,
    filter_by_supplier, filter_by_price_range, filter_by_quantity_range,
    filter_low_stock, filter_warehouses, filter_combined
)

# Сортиране – изнесено в отделен пакет
from sorting.product_sorters import (
    sort_by_name_logic, sort_by_price_desc_logic,
    bubble_sort_logic, selection_sort_logic
)

# Аналитика – изнесена в отделен пакет
from analytics.product_analytics import (
    calculate_average_price, calculate_total_inventory_value,
    get_most_expensive_product, get_cheapest_product,
    group_products_by_category
)


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
            supplier = self.supplier_controller.get_by_id(supplier_id)
            if supplier is None:
                raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")

    def _validate_categories(self, category_ids):
        if not category_ids:
            raise ValueError("Продуктът трябва да има поне една категория.")

        categories = []
        for cid in category_ids:
            category = self.category_controller.get_by_id(cid)
            if category is None:
                raise ValueError(f"Категория с ID {cid} не съществува.")
            categories.append(category)
        return categories

    def _log(self, user_id, action, message):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    #  ЗАРЕЖДАНЕ НА ПРОДУКТИТЕ ОТ JSON
    def _load_products(self):
        """ Контролерът не се интересува от вътрешната структура."""
        raw_data = self.repo.load()
        self.products = [Product.from_dict(p_data, self.category_controller) for p_data in raw_data]

    # CREATE PRODUCT
    def add(self, product_data: dict, user_id: str) -> Product:
        # Контролерът само дирижира процеса.

        # 1. Валидация (чрез външен компонент)
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

        # 2. Бизнес логика (Проверка за уникалност)
        if self._is_duplicate(product_data['name'], product_data.get('location_id', 'W1')):
            raise ValueError("Продуктът вече съществува в този склад.")

        # 3. Подготовка на зависимости (Categories & Supplier)
        categories = self._validate_categories(product_data['category_ids'])
        self._validate_supplier(product_data.get('supplier_id'))

        # 4. Създаване на модела
        now = datetime.now().isoformat()
        product = Product(
            product_id=self._generate_id(),
            name=product_data['name'],
            categories=categories,
            quantity=float(product_data['quantity']),
            unit=product_data['unit'],
            description=product_data['description'],
            price=float(product_data['price']),
            supplier_id=product_data.get('supplier_id'),
            location_id=product_data.get('location_id', 'W1'),
            tags=product_data.get('tags', []),
            created=now,
            modified=now
        )

        # 5. Персистиране и Логване
        self.products.append(product)
        self.save_changes()
        self._log(user_id, "ADD_PRODUCT", f"Успешно добавен: {product.name}")

        return product

    def _is_duplicate(self, name: str, location: str) -> bool:
        """ Помощен метод за бизнес логика """
        for p in self.products:
            if p.name.lower() == name.lower() and p.location_id == location:
                return True
        return False

    #  READ
    def get_all(self) -> List[Product]:
        return self.products

    def get_by_id(self, product_id: str) -> Optional[Product]:
        for p in self.products:
            if str(p.product_id) == str(product_id):
                return p
        return None

    def exists_by_name(self, name: str) -> bool:
        for p in self.products:
            if p.name.lower() == name.lower():
                return True
        return False

    # UPDATE
    def update_product(self, product_id: str, new_name: str, new_description: str, new_price: float,
                       new_quantity: float, user_id: str = "system"):
        """ Цялостно обновяване на продукт (Коригира липсващия метод за View-то). """
        p = self.get_by_id(product_id)
        if p is None:
            raise ValueError("Продуктът не е намерен.")

        # Проверка за уникалност на името (само ако името се променя)
        if new_name.lower() != p.name.lower() and self.exists_by_name(new_name):
            raise ValueError("Продукт с това име вече съществува.")

        # Валидация на новите данни
        ProductValidator.validate_name(new_name)
        ProductValidator.validate_description(new_description)
        ProductValidator.validate_price(new_price)
        if float(new_quantity) < 0:
            raise ValueError("Количеството не може да бъде отрицателно.")

        # Обновяване на стойностите
        p.name = new_name
        p.description = new_description
        p.price = round(float(new_price), 2)
        p.quantity = round(float(new_quantity), 2)

        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Обновен продукт: {p.name} (ID: {product_id})")
        return True

    def update_name(self, product_id: str, new_name: str, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if p is None:
            raise ValueError("Продуктът не е намерен.")

        if new_name.lower() != p.name.lower() and self.exists_by_name(new_name):
            raise ValueError("Продукт с това име вече съществува.")

        ProductValidator.validate_name(new_name)
        p.name = new_name
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated name of product ID {product_id} to '{new_name}'")
        return True

    def update_description(self, product_id: str, new_description: str, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if p is None:
            raise ValueError("Продуктът не е намерен.")

        ProductValidator.validate_description(new_description)
        p.description = new_description
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated description of product ID {product_id}")
        return True

    def update_categories(self, product_id: str, new_category_ids: List[str], user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if p is None:
            raise ValueError("Продуктът не е намерен.")

        categories = self._validate_categories(new_category_ids)
        p.categories = categories
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated categories of product ID {product_id}")
        return True

    def update_supplier(self, product_id: str, supplier_id: str, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if p is None:
            raise ValueError("Продуктът не е намерен.")

        self._validate_supplier(supplier_id)
        p.supplier_id = supplier_id
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated supplier of product ID {product_id}")
        return True

    def update_price(self, product_id: str, new_price: float, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if p is None:
            raise ValueError("Продуктът не е намерен.")

        ProductValidator.validate_price(new_price)
        p.price = round(float(new_price), 2)
        p.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_PRODUCT", f"Updated price of product ID {product_id} to {new_price}")
        return True

    def update_product(self, product_id: str, new_name: str, new_description: str,
                       new_price: float, new_quantity: float) -> bool:
        """Комбинирано обновяване на основните полета на продукта."""

        product = self.get_by_id(product_id)
        if product is None:
            raise ValueError("Продуктът не е намерен.")

        # Име
        if new_name and new_name != product.name:
            ProductValidator.validate_name(new_name)
            product.name = new_name

        # Описание
        if new_description and new_description != product.description:
            ProductValidator.validate_description(new_description)
            product.description = new_description

        # Цена
        ProductValidator.validate_price(new_price)
        product.price = round(float(new_price), 2)

        # Количество
        ProductValidator.validate_quantity(new_quantity)
        product.quantity = round(float(new_quantity), 2)

        # Обновяване на дата
        product.update_modified()

        # Записване
        self.save_changes()

        return True

    #  QUANTITY
    def increase_quantity(self, product_id: str, amount: float, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if p is None:
            raise ValueError("Продуктът не е намерен.")

        if amount <= 0:
            raise ValueError("Количество трябва да е положително.")

        p.quantity = round(p.quantity + float(amount), 2)
        p.update_modified()
        self.save_changes()
        self._log(user_id, "INCREASE_QUANTITY", f"Added {amount} units to product ID {product_id}")
        return True

    def decrease_quantity(self, product_id: str, amount: float, user_id: str) -> bool:
        p = self.get_by_id(product_id)
        if p is None:
            raise ValueError("Продуктът не е намерен.")

        if amount <= 0:
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
        before = len(self.products)
        self.products = [p for p in self.products if str(p.product_id) != str(product_id)]

        if len(self.products) < before:
            self.save_changes()
            self._log(user_id, "DELETE_PRODUCT", f"Deleted product ID {product_id}")
            return True

        return False

    def remove_by_name(self, name: str, user_id: str) -> bool:
        name = name.lower()
        before = len(self.products)
        self.products = [p for p in self.products if p.name.lower() != name]

        if len(self.products) < before:
            self.save_changes()
            self._log(user_id, "DELETE_PRODUCT", f"Deleted product '{name}'")
            return True
        return False

    def group_by_category_display(self):
        """Връща данни във формат, удобен за визуализация във View."""
        groups = self.group_by_category()
        result = {}

        for category_id, products in groups.items():
            items = []
            for p in products:
                items.append({
                    "name": p.name,
                    "location": p.location_id,
                    "quantity": p.quantity,
                    "unit": p.unit
                })
            result[category_id] = items

        return result

    #  FILTERS
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
        return calculate_average_price(self.products)

    def total_values(self) -> float:
        return calculate_total_inventory_value(self.products)

    def most_expensive(self) -> Optional[Product]:
        return get_most_expensive_product(self.products)

    def cheapest(self) -> Optional[Product]:
        return get_cheapest_product(self.products)

    def group_by_category(self) -> dict:
        return group_products_by_category(self.products)

    # SORTING
    def sort_by_name(self) -> List[Product]:
        return sort_by_name_logic(self.products)

    def sort_by_price_desc(self) -> List[Product]:
        return sort_by_price_desc_logic(self.products)

    def bubble_sort(self, key=lambda p: p.price, reverse=True) -> List[Product]:
        return bubble_sort_logic(self.products, key, reverse)

    def selection_sort(self, key=lambda p: p.price, reverse=True) -> List[Product]:
        return selection_sort_logic(self.products, key, reverse)

    #  SAVE
    def save_changes(self) -> None:
        self.repo.save([p.to_dict() for p in self.products])