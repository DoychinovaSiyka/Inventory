from typing import List, Optional
from models.product import Product
from validators.product_validator import ProductValidator


class ProductController:
    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.activity_log_controller = activity_log_controller
        self.products: List[Product] = []
        self._reload()

    def _reload(self):
        data = self.repo.load() or []
        self.products = []
        for p in data:
            self.products.append(Product.from_dict(p, self.category_controller))

    def save_changes(self):
        data = []
        for p in self.products:
            data.append(p.to_dict())
        self.repo.save(data)

    def _log(self, user_id, action, message):
        if self.activity_log_controller and user_id:
            self.activity_log_controller.log_action(user_id, action, message)

    def add(self, product_data: dict, user_id: str) -> Product:
        name = ProductValidator.validate_name(product_data['name'])
        ProductValidator.validate_unique_name(name, self.products)

        description = ProductValidator.validate_description(product_data.get('description', ""))

        unit = ProductValidator.validate_unit(product_data.get('unit', 'бр.'))

        price = ProductValidator.parse_float(product_data['price'], "Цена")

        categories = []
        for cid in product_data.get('category_ids', []):
            cat = self.category_controller.get_by_id(cid)
            if cat:
                categories.append(cat)

        product = Product(product_id=None, name=name, categories=categories,
                          unit=unit, description=description, price=price)

        self.products.append(product)
        self.save_changes()

        self._log(user_id, "CREATE_PRODUCT", f"Продукт: {product.name} (ID: {product.product_id[:8]})")
        return product

    def get_by_id(self, product_id) -> Optional[Product]:
        pid_str = str(product_id or "").strip()
        if pid_str == "":
            return None

        for p in self.products:
            if p.product_id.startswith(pid_str):
                return p
        return None

    def delete_by_id(self, product_id, user_id):
        product = self.get_by_id(product_id)
        if not product:
            return False

        full_id = product.product_id
        name_tmp = product.name

        new_list = []
        for p in self.products:
            if p.product_id != full_id:
                new_list.append(p)

        self.products = new_list
        self.save_changes()

        self._log(user_id, "DELETE_PRODUCT", f"Продукт: {name_tmp} (ID: {full_id[:8]})")
        return True

    def update_product(self, product_id, new_name=None, new_description=None,
                       new_price=None, user_id=None):

        product = self.get_by_id(product_id)
        if not product:
            return False

        changes = []

        if new_name:
            ProductValidator.validate_name(new_name)
            ProductValidator.validate_unique_name(new_name, self.products, exclude_product_id=product.product_id)
            changes.append(f"име: {product.name} -> {new_name}")
            product.name = new_name
            product.update_modified()
        if new_description is not None:
            desc = ProductValidator.validate_description(new_description)
            product.description = desc
            product.update_modified()
            changes.append("описание: променено")
        if new_price is not None:
            price = ProductValidator.parse_float(new_price, "Цена")
            old_p = product.price
            product.price = price
            product.update_modified()
            changes.append(f"цена: {old_p} -> {price}")

        if changes:
            self.save_changes()
            self._log(user_id, "UPDATE_PRODUCT", f"Редакция {product.product_id[:8]}: " + ", ".join(changes))

        return True

    def search(self, keyword) -> List[Product]:
        clean_keyword = str(keyword or "").strip().lower()
        if clean_keyword == "":
            return self.get_all()

        result = []
        for p in self.products:
            if clean_keyword in p.name.lower():
                result.append(p)
                continue
            if clean_keyword in (p.description or "").lower():
                result.append(p)
                continue
            if clean_keyword in p.product_id.lower():
                result.append(p)

        return result

    def filter_by_category(self, category_id) -> List[Product]:
        cat = self.category_controller.get_by_id(category_id)
        if not cat:
            return []

        result = []
        for p in self.products:
            for c in p.categories:
                if c.category_id == cat.category_id:
                    result.append(p)
                    break

        return result

    def get_all(self) -> List[Product]:
        if self.products:
            return self.products
        return []
