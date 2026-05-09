from typing import List, Optional
from models.product import Product
from validators.product_validator import ProductValidator
from filters import product_filters
from analytics import product_analytics


class ProductController:
    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.products: List[Product] = []
        self._reload()

    def _reload(self):
        """Зарежда данните и ги превръща в обекти."""
        data = self.repo.load() or []
        self.products = [Product.from_dict(p, self.category_controller) for p in data]

    def save_changes(self):
        """Записва промените обратно в хранилището."""
        self.repo.save([p.to_dict() for p in self.products])

    def add(self, product_data: dict, user_id: str) -> Product:
        name = ProductValidator.validate_name(product_data['name'])
        ProductValidator.validate_unique_name(name, self.products)
        price = ProductValidator.parse_float(product_data['price'], "Цена")

        categories = []
        for cid in product_data.get('category_ids', []):
            cat = self.category_controller.get_by_id(cid)
            if cat:
                categories.append(cat)

        product = Product(product_id=None, name=name, categories=categories,
                          unit=product_data.get('unit', 'бр.'),
                          description=product_data.get('description', ""), price=price)
        self.products.append(product)
        self.save_changes()
        return product

    def get_by_id(self, product_id: str) -> Optional[Product]:
        pid = str(product_id or "").strip()
        if not pid: return None
        return next((p for p in self.products if p.product_id.startswith(pid)), None)

    def get_all(self) -> List[Product]:
        """Връща всички продукти."""
        return self.products



    def get_most_expensive(self) -> Optional[Product]:
        return product_analytics.get_most_expensive_product(self.products)

    def get_cheapest(self) -> Optional[Product]:
        """Връща най-евтиния продукт."""
        return product_analytics.get_cheapest_product(self.products)

    def get_average_price(self) -> float:
        """Връща средната цена на всички продукти."""
        return product_analytics.calculate_average_price(self.products)

    def get_total_value(self, inventory_controller) -> float:
        """Връща общата стойност на склада."""
        return product_analytics.calculate_total_inventory_value(self.products, inventory_controller)

    def get_products_grouped_by_category(self) -> dict:
        """Връща продуктите групирани по категории (активира аналитичната функция)."""
        return product_analytics.group_products_by_category(self.products)
    

    # ФИЛТРИ И ТЪРСЕНЕ
    def search(self, keyword: str) -> List[Product]:
        return product_filters.filter_combined(self.products, keyword=keyword)

    def filter_by_category(self, category_id) -> List[Product]:
        return product_filters.filter_combined(self.products, category_id=category_id)

    def delete_by_id(self, product_id, user_id):
        """Изтриване на продукт."""
        product = self.get_by_id(product_id)
        if not product: return False
        self.products = [p for p in self.products if p.product_id != product.product_id]
        self.save_changes()
        return True