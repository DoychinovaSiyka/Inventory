from typing import List, Optional
from models.product import Product
from validators.product_validator import ProductValidator
from filters import product_filters, product_sorters


class ProductController:
    """Управлява каталога с продукти. Синхронизиран с инвентара за безопасно триене."""
    def __init__(self, repo, category_controller, inventory_controller):
        self.repo = repo
        self.category_controller = category_controller
        self.inventory_controller = inventory_controller
        self.validator = ProductValidator()
        self.products: List[Product] = []
        self._reload()

    def _reload(self) -> None:
        """Зарежда продуктите от хранилището."""
        data = self.repo.load() or []
        self.products = [Product.from_dict(p, self.category_controller) for p in data]

    def save_changes(self) -> None:
        """Записва текущото състояние в базата/файла."""
        self.repo.save([p.to_dict() for p in self.products])

    def get_all(self) -> List[Product]:
        """всички налични продукти в каталога."""
        return self.products



    def get_by_id(self, product_id: str) -> Optional[Product]:
        """Намира продукт по пълно или частично ID."""
        pid = str(product_id).strip()
        if not pid:
            return None

        for p in self.products:
            if str(p.product_id) == pid:
                return p

        if len(pid) >= 4:
            for p in self.products:
                if str(p.product_id).startswith(pid):
                    return p
        return None


    def add(self, product_data: dict) -> Product:
        """Добавя нов продукт с пълна валидация на полетата."""
        name = self.validator.validate_name(product_data["name"])
        self.validator.validate_unique_name(name, self.products)

        price = self.validator.parse_float(product_data["price"], "Цена")
        unit = self.validator.validate_unit(product_data.get("unit", "бр."))
        description = product_data.get("description", "").strip()

        # превръщаме ID-тата в реални обекти
        categories = []
        raw_ids = product_data.get("category_ids", [])
        id_list = raw_ids if isinstance(raw_ids, list) else [raw_ids]
        for cid in id_list:
            cat = self.category_controller.get_by_id(cid)
            if cat:
                categories.append(cat)

        product = Product(product_id=None, name=name, categories=categories,
                          unit=unit, description=description, price=price)

        self.products.append(product)
        self.save_changes()
        return product

    def update(self, product_id: str, updates: dict) -> bool:
        """Обновява данни на продукт, като следи за уникалност на името."""
        product = self.get_by_id(product_id)
        if not product:
            return False

        # Обновяваме само подадените полета
        if "name" in updates:
            new_name = self.validator.validate_name(updates["name"])
            self.validator.validate_unique_name(new_name, self.products, exclude_product_id=product.product_id)
            product.name = new_name

        if "price" in updates:
            product.price = self.validator.parse_float(updates["price"], "Цена")

        if "description" in updates:
            product.description = updates["description"].strip()

        if "unit" in updates:
            product.unit = self.validator.validate_unit(updates["unit"])

        if "category_ids" in updates:
            new_cats = []
            for cid in updates["category_ids"]:
                cat = self.category_controller.get_by_id(cid)
                if cat:
                    new_cats.append(cat)
            product.categories = new_cats

        product.update_modified()
        self.save_changes()
        return True



    def delete_by_id(self, product_id: str) -> bool:
        """ Изтрива продукт само ако няма наличност в инвентара."""
        product = self.get_by_id(product_id)
        if not product:
            return False


        current_stock = self.inventory_controller.get_total_stock(product.product_id)
        if current_stock > 0:
            raise ValueError(f"Не може да изтриете '{product.name}', защото има наличност: {current_stock} {product.unit}")

        self.products = [p for p in self.products if p.product_id != product.product_id]
        self.save_changes()
        return True


    def search(self, keyword: str) -> List[Product]:
        """Търсене по ключова дума в името или описанието."""
        return product_filters.filter_combined(self.products, keyword=keyword)

    def filter_by_category_hierarchy(self, category_ids: List[str]) -> List[Product]:
        """Филтрира продукти, принадлежащи към списък от категории."""
        return product_filters.filter_combined(self.products, category_ids=category_ids)


    def get_custom_sort(self, sort_type="price", algorithm="selection", reverse=True) -> List[Product]:
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
            return product_sorters.bubble_sort(products_copy, key=key_fn, reverse=reverse)

        return product_sorters.selection_sort(products_copy, key=key_fn, reverse=reverse)