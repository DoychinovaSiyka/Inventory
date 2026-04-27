from typing import Optional, List
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
    """Контролерът отговаря за работа с продуктите – добавяне, редакция, триене и справки."""
    def __init__(self, repo, category_controller, activity_log_controller=None):
        # Запазваме нужните контролери и хранилището
        self.repo = repo
        self.category_controller = category_controller
        self.activity_log = activity_log_controller
        self.products: List[Product] = []  # държим всички продукти в паметта
        self._load_products()

        # контролерите се задават отвън, когато са налични
        self.supplier_controller = None
        self.inventory_controller = None
        self.movement_controller = None

    # Записваме действие в логовете, ако има лог контролер
    def _log(self, user_id, action, message):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    # Зареждаме продуктите от файла/базата
    def _load_products(self):
        raw = self.repo.load()
        self.products = [Product.from_dict(p_data, self.category_controller)
                         for p_data in raw]

    # Операции за четене
    def get_all(self) -> List[Product]:
        return self.products

    def get_by_id(self, product_id: str) -> Optional[Product]:
        product_id = str(product_id)
        for p in self.products:
            if str(p.product_id) == product_id:
                return p
        return None

    def get_by_name(self, name: str) -> Optional[Product]:
        name = name.strip().lower()
        for p in self.products:
            if p.name.lower() == name:
                return p
        return None

    def exists_by_name(self, name: str) -> bool:
        return any(p.name.lower() == name.lower() for p in self.products)

    def add(self, product_data: dict, user_id: str) -> Product:
        """ Добавяме нов продукт. Началното количество се прави чрез IN движение. """
        ProductValidator.validate_category_exists(product_data['category_ids'], self.category_controller)
        ProductValidator.validate_supplier_exists(product_data.get('supplier_id'), self.supplier_controller)
        ProductValidator.validate_name(product_data['name'])

        now = Product.now()

        # Взимаме обектите на категориите
        categories = [self.category_controller.get_by_id(cid) for cid in product_data['category_ids']]

        # Създаваме продукта
        product = Product(product_id=self._generate_id(), name=product_data['name'],
                          categories=categories, unit=product_data['unit'],
                          description=product_data['description'], price=float(product_data['price']),
                          supplier_id=product_data.get('supplier_id'), tags=product_data.get('tags', []),
                          location_id=product_data.get('location_id'), created=now, modified=now)

        # Добавяме продукта в списъка
        self.products.append(product)
        self.save_changes()
        self._log(user_id, "ADD_PRODUCT", f"Добавен продукт: {product.name}")

        # Ако има начално количество – правим IN движение
        quantity = product_data.get("quantity")
        location_id = product_data.get("location_id")

        if quantity and location_id and self.movement_controller:
            qty = float(quantity)
            if qty > 0:
                self.movement_controller.add(product_id=product.product_id, user_id=user_id,
                                             location_id=location_id, movement_type="IN", quantity=str(qty),
                                             description="Начално зареждане при създаване на продукт",
                                             price=str(product.price), supplier_id=product.supplier_id or "system")

        return product

    # Редакция на продукт
    def update_product(self, product_id: str, new_name: Optional[str], new_description: Optional[str],
                       new_price: float, new_quantity: Optional[float] = None, new_unit: Optional[str] = None,
                       new_category_ids: Optional[List[str]] = None, new_location_id: Optional[str] = None,
                       new_supplier_id: Optional[str] = None, new_tags: Optional[List[str]] = None,
                       user_id: str = "system") -> bool:

        product = ProductValidator.validate_product_exists(product_id, self)
        has_changes = False

        # Име
        if new_name is not None:
            new_name_clean = new_name.strip()
            if new_name_clean != product.name:
                ProductValidator.validate_name(new_name_clean)
                product.name = new_name_clean
                has_changes = True

        # Описание
        if new_description is not None:
            new_desc_clean = new_description.strip()
            if new_desc_clean != product.description:
                product.description = ProductValidator.validate_description(new_desc_clean)
                has_changes = True

        # Цена
        new_price_valid = ProductValidator.validate_price(new_price)
        if new_price_valid != product.price:
            product.price = new_price_valid
            has_changes = True

        # Количество чрез движение
        if new_quantity is not None and self.inventory_controller and self.movement_controller:
            current_stock = self.inventory_controller.get_total_stock(product_id)
            diff = float(new_quantity) - float(current_stock)

            if abs(diff) > 0.001:
                m_type = "IN" if diff > 0 else "OUT"
                self.movement_controller.add(product_id=product_id, user_id=user_id,
                                             location_id=new_location_id or product.location_id or "W1", movement_type=m_type,
                                             quantity=str(abs(diff)), description=f"Корекция ({m_type}) от редакция",
                                             price=str(product.price), supplier_id=product.supplier_id or "system")
                has_changes = True


        if new_unit is not None:
            new_unit_clean = new_unit.strip()
            if new_unit_clean and new_unit_clean != product.unit:
                product.unit = ProductValidator.validate_unit(new_unit_clean)
                has_changes = True

        # Категории
        if new_category_ids is not None:
            ProductValidator.validate_category_exists(new_category_ids, self.category_controller)
            new_categories = [self.category_controller.get_by_id(cid) for cid in new_category_ids]
            if new_categories != product.categories:
                product.categories = new_categories
                has_changes = True

        # Локация
        if new_location_id is not None and new_location_id != product.location_id:
            product.location_id = new_location_id
            has_changes = True

        # Доставчик
        if new_supplier_id is not None and new_supplier_id != product.supplier_id:
            ProductValidator.validate_supplier_exists(new_supplier_id, self.supplier_controller)
            product.supplier_id = new_supplier_id
            has_changes = True

        # Тагове
        if new_tags is not None:
            if not isinstance(new_tags, list):
                raise ValueError("Tags трябва да са списък.")
            if new_tags != product.tags:
                product.tags = new_tags
                has_changes = True

        # Запис само ако има промени
        if has_changes:
            product.update_modified()
            self.save_changes()
            self._log(user_id, "EDIT_PRODUCT", f"Обновен продукт: {product.name}")

        return True

    # Изтриване на продукт
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

    # Информация за наличности
    def get_total_stock(self, product_id: str) -> float:
        if not self.inventory_controller:
            return 0.0
        return self.inventory_controller.get_total_stock(product_id)

    # Търсене и филтриране
    def search(self, keyword: str) -> List[Product]:
        return filter_search(self.products, keyword)

    def filter_by_multiple_category_ids(self, category_ids: List[str]) -> List[Product]:
        return filter_by_multiple_category_ids(self.products, category_ids)

    def check_low_stock(self, threshold: float = 5) -> List[Product]:
        return filter_low_stock(self.products, threshold, self.inventory_controller)

    def search_by_price_range(self, min_price=None, max_price=None):
        return filter_by_price_range(self.products, min_price, max_price)

    def search_by_category(self, category_id: str):
        return filter_by_category(self.products, category_id)

    def search_by_supplier(self, supplier_id: str):
        return filter_by_supplier(self.products, supplier_id)

    def search_combined(self, keyword=None, min_price=None, max_price=None,
                        min_quantity=None, max_quantity=None,
                        category_id=None, supplier_id=None, location_id=None):

        return filter_combined(self.products, self.inventory_controller, keyword=keyword,
                               min_price=min_price, max_price=max_price,
                               min_quantity=min_quantity, max_quantity=max_quantity,
                               category_id=category_id, supplier_id=supplier_id, location_id=location_id)


    def get_warehouses_with_product(self, product_name: str):
        return filter_warehouses(self.products, product_name)

    # Анализи и статистики
    def average_price(self) -> float:
        return calculate_average_price(self.products)

    def total_values(self) -> float:
        return calculate_total_inventory_value(self.products, self.inventory_controller)

    def most_expensive(self) -> Optional[Product]:
        return get_most_expensive_product(self.products)

    def cheapest(self) -> Optional[Product]:
        return get_cheapest_product(self.products)

    def group_by_category(self) -> dict:
        return group_products_by_category(self.products)

    def sort_by_name(self) -> List[Product]:
        return sort_by_name_logic(self.products)

    def sort_by_price_desc(self) -> List[Product]:
        return sort_by_price_desc_logic(self.products)

    def bubble_sort(self, key=lambda p: p.price, reverse=True) -> List[Product]:
        return bubble_sort_logic(self.products, key, reverse)

    def selection_sort(self, key=lambda p: p.price, reverse=True) -> List[Product]:
        return selection_sort_logic(self.products, key, reverse)

    # Записване на промените
    def save_changes(self) -> None:
        self.repo.save([p.to_dict() for p in self.products])
