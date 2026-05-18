from typing import List, Optional
from models.product import Product
from validators.product_validator import ProductValidator
from filters import product_filters, product_sorters
from controllers.abstract_controller import AbstractController


class ProductController(AbstractController):
    """Управлява каталога с продукти и гарантира бизнес логиката."""

    def __init__(self, repo, category_controller):
        self.category_controller = category_controller
        self.validator = ProductValidator()
        super().__init__(repo)
        self.products = self.load() or []


    def from_dict(self, data):
        return Product.from_dict(data, self.category_controller)

    def to_dict(self, obj):
        return obj.to_dict()

    def _save_products(self):
        self.save(self.products)

    def get_all(self) -> List[Product]:
        """Връща всички налични продукти."""
        return self.products



    def get_by_id(self, product_id: str) -> Optional[Product]:
        pid = str(product_id or "").strip().lower()
        if not pid:
            return None

        for p in self.products:
            full_id = str(p.product_id).lower()
            short_id = full_id[:8]
            if pid == short_id or pid == full_id:
                return p
        return None



    def validate_field(self, field_type: str, value: str, exclude_id: str = None) -> Optional[str]:

        try:
            if field_type == "name":
                name = self.validator.validate_name(value)
                self.validator.validate_unique_name(name, self.products, exclude_product_id=exclude_id)
            elif field_type == "price":
                self.validator.parse_float(value, "Цена")
            elif field_type == "description":
                self.validator.validate_description(value)
            elif field_type == "unit":
                self.validator.validate_unit(value)
            elif field_type == "category":
                if not self.category_controller.get_by_id(value):
                    return "Невалидна категория."
            return None

        except ValueError as e:
            return str(e)

        except Exception as e:
            return f"Неочаквана грешка: {e}"



    def add(self, product_data: dict) -> Product:
        name = self.validator.validate_name(product_data["name"])
        self.validator.validate_unique_name(name, self.products)

        price = self.validator.parse_float(product_data["price"], "Цена")
        unit = self.validator.validate_unit(product_data.get("unit", "бр."))
        description = self.validator.validate_description(product_data.get("description", ""))


        category_ids = product_data.get("category_ids", [])
        categories = []
        for cid in (category_ids if isinstance(category_ids, list) else [category_ids]):
            cat = self.category_controller.get_by_id(cid)
            if cat:
                categories.append(cat)

        if not categories and category_ids:
            raise ValueError("Избраните категории са невалидни.")

        product = Product(product_id=None, name=name, categories=categories,
                          unit=unit, description=description, price=price)

        self.products.append(product)
        self._save_products()
        return product



    def update(self, product_id: str, updates: dict) -> bool:
        product = self.get_by_id(product_id)
        if not product:
            return False

        if "name" in updates:
            new_name = self.validator.validate_name(updates["name"])
            self.validator.validate_unique_name(new_name, self.products, exclude_product_id=product.product_id)
            product.name = new_name

        if "price" in updates:
            product.price = self.validator.parse_float(updates["price"], "Цена")

        if "description" in updates:
            product.description = self.validator.validate_description(updates["description"])

        if "unit" in updates:
            product.unit = self.validator.validate_unit(updates["unit"])

        if "category_ids" in updates:
            new_cats = []
            for cid in updates["category_ids"]:
                cat = self.category_controller.get_by_id(cid)
                if cat:
                    new_cats.append(cat)
            if not new_cats and updates["category_ids"]:
                raise ValueError("Категориите не са валидни.")
            product.categories = new_cats

        product.update_modified()
        self._save_products()
        return True



    def delete_by_id(self, product_id: str) -> bool:
        """Изтрива продукт от каталога."""
        product = self.get_by_id(product_id)
        if not product:
            return False

        self.products = [p for p in self.products if p.product_id != product.product_id]
        self._save_products()
        return True



    def search(self, keyword: str) -> List[Product]:
        return product_filters.filter_combined(self.products, keyword=keyword)


    def filter_by_category_hierarchy(self, category_ids: List[str]) -> List[Product]:
        return product_filters.filter_combined(self.products, category_ids=category_ids)




    def get_custom_sort(self, sort_type="price", algorithm="quick", reverse=True) -> List[Product]:
        if sort_type == "name":
            key_fn = lambda p: p.name.lower()
        elif sort_type == "price":
            key_fn = lambda p: p.price
        else:
            key_fn = lambda p: p.name.lower()

        products_copy = self.products[:]


        if sort_type == "name":
            return product_sorters.merge_sort(products_copy, key=key_fn, reverse=reverse)


        if algorithm == "quick":
            return product_sorters.quick_sort(products_copy, key=key_fn, reverse=reverse)
        else:
            return product_sorters.merge_sort(products_copy, key=key_fn, reverse=reverse)
