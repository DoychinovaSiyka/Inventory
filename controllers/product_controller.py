from typing import List, Optional
from models.product import Product
from validators.product_validator import ProductValidator
from filters import product_filters
from analytics import product_analytics
from sorting import product_sorters


class ProductController:
    def __init__(self, repo, category_controller, inventory_controller):
        self.repo = repo
        self.category_controller = category_controller
        self.inventory_controller = inventory_controller
        self.products: List[Product] = []
        self._reload()

    def _reload(self):
        data = self.repo.load() or []
        self.products = [Product.from_dict(p, self.category_controller) for p in data]

    def save_changes(self):
        self.repo.save([p.to_dict() for p in self.products])

    def add(self, product_data: dict) -> Product:
        name = ProductValidator.validate_name(product_data["name"])
        ProductValidator.validate_unique_name(name, self.products)
        price = ProductValidator.parse_float(product_data["price"], "Цена")
        unit = ProductValidator.validate_unit(product_data.get("unit", "бр."))

        categories = []
        raw_ids = product_data.get("category_ids", [])
        for cid in (raw_ids if isinstance(raw_ids, list) else [raw_ids]):
            cat = self.category_controller.get_by_id(cid)
            if cat: categories.append(cat)

        product = Product(None, name, categories, unit, product_data.get("description", ""), price)
        self.products.append(product)
        self.save_changes()
        return product

    def get_by_id(self, product_id: str) -> Optional[Product]:
        pid = str(product_id or "").strip()
        return next((p for p in self.products if p.product_id.startswith(pid)), None)

    def get_all(self) -> List[Product]:
        return self.products

    def search(self, keyword: str) -> List[Product]:
        return product_filters.filter_combined(self.products, keyword=keyword)

    def filter_by_category(self, category_id: str) -> List[Product]:
        return product_filters.filter_combined(self.products, category_id=category_id)

    def delete_by_id(self, product_id: str) -> bool:
        product = self.get_by_id(product_id)
        if not product: return False
        self.products = [p for p in self.products if p.product_id != product.product_id]
        self.save_changes()
        return True

    def get_formatted_grouped_by_category(self) -> dict:
        """Логика за групиране и форматиране (бившият ViewModel)."""
        grouped_data = product_analytics.group_products_by_category(self.products)
        result = {}
        for cat_name, products_list in grouped_data.items():
            result[cat_name] = [{
                "name": p.name,
                "quantity": self.inventory_controller.get_total_stock(p.product_id),
                "unit": p.unit,
                "price": f"{p.price:.2f}"
            } for p in products_list]
        return result


    def get_sorted_by_name(self):
        return product_sorters.sort_by_name_logic(self.products[:])

    def get_sorted_by_price(self, reverse=True):
        return product_sorters.sort_by_price_desc_logic(self.products[:])

    def get_sorted_by_quantity(self, inventory_controller, algorithm="bubble", reverse=True):
        """Сортиране по наличност чрез подаден алгоритъм (Bubble или Selection)."""
        key_fn = lambda p: inventory_controller.get_total_stock(p.product_id)

        products_copy = self.products[:]
        if algorithm == "bubble":
            return product_sorters.bubble_sort_logic(products_copy, key=key_fn, reverse=reverse)
        return product_sorters.selection_sort_logic(products_copy, key=key_fn, reverse=reverse)

    def get_custom_sort(self, sort_type="price", algorithm="selection", reverse=True):
        """Сортиране по избран критерий (име, цена, количество)."""
        if sort_type == "name":
            key_fn = lambda p: p.name.lower()
        elif sort_type == "price":
            key_fn = lambda p: p.price
        elif sort_type == "quantity":
            key_fn = lambda p: self.inventory_controller.get_total_stock(p.product_id)
        else:
            key_fn = lambda p: p.name.lower()

        products_copy = self.products[:]


        if algorithm == "bubble":
            return product_sorters.bubble_sort_logic(products_copy, key=key_fn, reverse=reverse)
        else:
            return product_sorters.selection_sort_logic(products_copy, key=key_fn, reverse=reverse)
