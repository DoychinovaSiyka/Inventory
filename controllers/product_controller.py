from typing import List, Optional
from models.product import Product
from validators.product_validator import ProductValidator
from filters import product_filters
from analytics import product_analytics
from sorting import product_sorters


class ProductController:
    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.products: List[Product] = []
        self._reload()


    def _reload(self):
        """Зарежда данните от JSON и ги превръща в Product обекти."""
        data = self.repo.load() or []
        self.products = [Product.from_dict(p, self.category_controller) for p in data]

    def save_changes(self):
        """Записва всички промени обратно в JSON хранилището."""
        self.repo.save([p.to_dict() for p in self.products])

    def add(self, product_data: dict, user_id: str) -> Product:
        """Валидира и добавя нов продукт."""
        name = ProductValidator.validate_name(product_data['name'])
        ProductValidator.validate_unique_name(name, self.products)
        price = ProductValidator.parse_float(product_data['price'], "Цена")

        categories = []
        for cid in product_data.get('category_ids', []):
            cat = self.category_controller.get_by_id(cid)
            if cat:
                categories.append(cat)

        product = Product(
            product_id=None,
            name=name,
            categories=categories,
            unit=product_data.get('unit', 'бр.'),
            description=product_data.get('description', ""),
            price=price
        )

        self.products.append(product)
        self.save_changes()
        return product

    def get_by_id(self, product_id: str) -> Optional[Product]:
        """Намира продукт по ID или част от ID."""
        pid = str(product_id or "").strip()
        if not pid:
            return None
        return next((p for p in self.products if p.product_id.startswith(pid)), None)

    def get_all(self) -> List[Product]:
        """Връща всички продукти."""
        return self.products

    def delete_by_id(self, product_id: str, user_id: str) -> bool:
        """Изтрива продукт по ID."""
        product = self.get_by_id(product_id)
        if not product:
            return False
        self.products = [p for p in self.products if p.product_id != product.product_id]
        self.save_changes()
        return True


    def search(self, keyword: str) -> List[Product]:
        """Търсене по име или описание."""
        return product_filters.filter_combined(self.products, keyword=keyword)

    def filter_by_category(self, category_id: str) -> List[Product]:
        """Филтриране по категория."""
        return product_filters.filter_combined(self.products, category_id=category_id)


    def get_sorted_by_name(self) -> List[Product]:
        return product_sorters.sort_by_name_logic(self.products[:])

    def get_sorted_by_price(self, reverse=True) -> List[Product]:
        if reverse:
            return product_sorters.sort_by_price_desc_logic(self.products[:])
        return product_sorters.bubble_sort_logic(
            self.products[:],
            key=lambda p: p.price,
            reverse=False
        )

    def get_custom_sort(self, sort_type: str, algorithm: str = "selection", reverse=False) -> List[Product]:
        """Универсално сортиране по атрибут и алгоритъм."""
        key_fn = lambda p: getattr(p, sort_type)

        if algorithm == "bubble":
            return product_sorters.bubble_sort_logic(self.products[:], key=key_fn, reverse=reverse)
        return product_sorters.selection_sort_logic(self.products[:], key=key_fn, reverse=reverse)


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
