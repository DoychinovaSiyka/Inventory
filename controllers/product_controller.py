from typing import List, Optional
from models.product import Product
from validators.product_validator import ProductValidator
from filters import product_filters
from analytics import product_analytics
from sorting import product_sorters
from sorting.product_sorters import bubble_sort_logic, selection_sort_logic


class ProductController:
    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.products: List[Product] = []
        self._reload()

    def _reload(self):
        # Зареждаме продуктите от файла и ги превръщаме в обекти
        data = self.repo.load() or []
        self.products = []

        for p_dict in data:
            try:
                obj = Product.from_dict(p_dict, self.category_controller)
                self.products.append(obj)
            except Exception as e:
                print(f"Проблем при зареждане на продукт: {e}")

    def save_changes(self):
        # Записваме всички продукти обратно в JSON
        self.repo.save([p.to_dict() for p in self.products])

    def add(self, product_data: dict, user_id: str) -> Product:
        # Валидираме име и цена
        name = ProductValidator.validate_name(product_data["name"])
        ProductValidator.validate_unique_name(name, self.products)
        price = ProductValidator.parse_float(product_data["price"], "Цена")

        # Превръщаме ID-тата на категориите в Category обекти
        categories = []
        raw_ids = product_data.get("category_ids", [])

        if isinstance(raw_ids, str):
            raw_ids = [raw_ids]

        for cid in raw_ids:
            cat = self.category_controller.get_by_id(cid)
            if cat:
                categories.append(cat)

        # Създаваме нов продукт
        product = Product(
            product_id=None,
            name=name,
            categories=categories,
            unit=product_data.get("unit", "бр."),
            description=product_data.get("description", ""),
            price=price
        )

        self.products.append(product)
        self.save_changes()
        return product

    def get_by_id(self, product_id: str) -> Optional[Product]:
        # Търсим продукт по ID (или начало на ID)
        pid = str(product_id or "").strip()
        if not pid:
            return None
        return next((p for p in self.products if p.product_id.startswith(pid)), None)

    def get_all(self) -> List[Product]:
        # Връщаме всички продукти
        return self.products

    def filter_by_category(self, category_id: str) -> List[Product]:
        # Филтрираме по ID на категория
        if not category_id:
            return self.products

        target = str(category_id).strip()
        results = []

        for p in self.products:
            for cat in getattr(p, "categories", []):
                current_id = str(getattr(cat, "category_id", cat)).strip()
                if current_id == target:
                    results.append(p)
                    break

        return results

    def search(self, keyword: str) -> List[Product]:
        # Търсене по име или описание
        if not keyword:
            return self.products
        return product_filters.filter_combined(self.products, keyword=keyword)

    def delete_by_id(self, product_id: str, user_id: str) -> bool:
        # Изтриваме продукт по ID
        product = self.get_by_id(product_id)
        if not product:
            return False

        self.products = [p for p in self.products if p.product_id != product.product_id]
        self.save_changes()
        return True

    # Сортиране

    def get_sorted_by_name(self) -> List[Product]:
        # Сортиране по име
        return product_sorters.sort_by_name_logic(self.products[:])

    def get_sorted_by_price(self, reverse=True) -> List[Product]:
        # Сортиране по цена
        if reverse:
            return product_sorters.sort_by_price_desc_logic(self.products[:])
        return product_sorters.bubble_sort_logic(self.products[:], key=lambda p: p.price, reverse=False)

    def get_sorted_by_quantity(self, inventory_controller, algorithm="bubble", reverse=True) -> List[Product]:
        # Сортиране по наличност
        products_copy = self.products[:]

        def get_stock(p):
            return inventory_controller.get_total_stock(p.product_id)

        if algorithm == "bubble":
            return bubble_sort_logic(products_copy, key=get_stock, reverse=reverse)
        if algorithm == "selection":
            return selection_sort_logic(products_copy, key=get_stock, reverse=reverse)

        products_copy.sort(key=get_stock, reverse=reverse)
        return products_copy

    def get_custom_sort(self, sort_type: str, algorithm: str = "selection", reverse=False) -> List[Product]:
        # Универсално сортиране по атрибут
        key_fn = lambda p: getattr(p, sort_type)

        if algorithm == "bubble":
            return product_sorters.bubble_sort_logic(self.products[:], key=key_fn, reverse=reverse)

        return product_sorters.selection_sort_logic(self.products[:], key=key_fn, reverse=reverse)

    # Анализи

    def get_most_expensive(self) -> Optional[Product]:
        return product_analytics.get_most_expensive_product(self.products)

    def get_cheapest(self) -> Optional[Product]:
        return product_analytics.get_cheapest_product(self.products)

    def get_average_price(self) -> float:
        return product_analytics.calculate_average_price(self.products)

    def get_total_value(self, inventory_controller) -> float:
        return product_analytics.calculate_total_inventory_value(self.products, inventory_controller)

    def get_products_grouped_by_category(self) -> dict:
        return product_analytics.group_products_by_category(self.products)
