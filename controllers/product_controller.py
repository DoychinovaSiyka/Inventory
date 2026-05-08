from typing import List, Optional
from models.product import Product
from validators.product_validator import ProductValidator
# Импортираме филтър модула под кратко име pf (product filters)
import filters.product_filters as pf


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

    def search(self, keyword: str) -> List[Product]:
        """Търсене чрез външния филтър модул."""
        return pf.filter_search(self.products, keyword)

    def filter_by_category(self, category_id) -> List[Product]:
        """Филтриране по категория чрез външния филтър модул."""
        # Подготовка на ID-тата (в случай че не са списък)
        if not isinstance(category_id, list):
            cat = self.category_controller.get_by_id(category_id)
            category_id = [cat.category_id] if cat else []

        return pf.filter_by_category(self.products, category_id)

    def get_by_id(self, product_id: str) -> Optional[Product]:
        """Намира продукт по ID (или по начало на ID)."""
        pid = str(product_id or "").strip()
        # Използваме next() за по-чист код без излишен for цикъл тук
        return next((p for p in self.products if p.product_id.startswith(pid)), None)

    def add(self, product_data: dict, user_id: str) -> Product:
        """Добавяне на нов продукт с валидация."""
        name = ProductValidator.validate_name(product_data['name'])
        ProductValidator.validate_unique_name(name, self.products)
        price = ProductValidator.parse_float(product_data['price'], "Цена")

        # Намираме обектите на категориите
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

    def update_product(self, product_id, **kwargs):
        """Обновяване на продукт."""
        product = self.get_by_id(product_id)
        if not product:
            return False

        if 'new_name' in kwargs and kwargs['new_name']:
            name = ProductValidator.validate_name(kwargs['new_name'])
            ProductValidator.validate_unique_name(name, self.products, exclude_product_id=product.product_id)
            product.name = name

        if 'new_price' in kwargs and kwargs['new_price'] is not None:
            product.price = ProductValidator.parse_float(kwargs['new_price'], "Цена")

        if 'new_description' in kwargs:
            product.description = ProductValidator.validate_description(kwargs['new_description'])

        product.update_modified()
        self.save_changes()
        return True

    def delete_by_id(self, product_id, user_id):
        """Изтриване на продукт."""
        product = self.get_by_id(product_id)
        if not product:
            return False

        self.products = [p for p in self.products if p.product_id != product.product_id]
        self.save_changes()
        return True

    def get_all(self) -> List[Product]:
        """Връща всички продукти."""
        return self.products