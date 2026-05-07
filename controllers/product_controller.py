from models.product import Product
from validators.product_validator import ProductValidator


class ProductController:
    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.activity_log_controller = activity_log_controller

        # Зареждаме продуктите с пълни UUID от JSON
        data = self.repo.load() or []
        self.products = [Product.from_dict(p, self.category_controller) for p in data]

    def save_changes(self):
        data = [p.to_dict() for p in self.products]
        self.repo.save(data)

    def _log(self, user_id, action, message):
        if self.activity_log_controller and user_id:
            self.activity_log_controller.log_action(user_id, action, message)

    def add(self, product_data: dict, user_id: str) -> Product:
        ProductValidator.validate_name(product_data['name'])

        categories = []
        for cid in product_data.get('category_ids', []):
            cat = self.category_controller.get_by_id(cid)
            if cat:
                categories.append(cat)

        product = Product(product_id=None, name=product_data['name'], categories=categories,
                          unit=product_data.get('unit', 'бр.'),
                          description=product_data.get('description', ''), price=float(product_data['price']))

        self.products.append(product)
        self.save_changes()

        short_id = product.product_id[:8]
        self._log(user_id, "CREATE_PRODUCT", f"Продукт: {product.name} (ID: {short_id})")
        return product

    def get_by_id(self, product_id):
        pid_str = str(product_id).strip()
        if not pid_str:
            return None

        for p in self.products:
            if p.product_id.startswith(pid_str):
                return p
        return None

    def delete_by_id(self, product_id, user_id):
        product = self.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не е намерен.")

        name_tmp = product.name
        full_id = product.product_id

        self.products.remove(product)
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
            changes.append(f"име: {product.name} -> {new_name}")
            product.name = new_name
            product.update_modified()

        if new_description is not None:
            product.description = new_description
            product.update_modified()

        if new_price is not None:
            old_p = product.price
            product.price = float(new_price)
            changes.append(f"цена: {old_p} -> {new_price}")
            product.update_modified()

        if changes:
            self.save_changes()
            self._log(user_id, "UPDATE_PRODUCT", f"Редакция {product.product_id[:8]}: " + ", ".join(changes))
        return True

    def search(self, keyword):
        if not keyword:
            return self.products
        keyword = keyword.lower()
        return [p for p in self.products if keyword in p.name.lower() or
                keyword in (p.description or "").lower() or
                keyword in p.product_id.lower()]  # Позволяваме търсене и по ID

    def filter_by_category(self, category_id):
        cat = self.category_controller.get_by_id(category_id)
        if not cat:
            return []
        target_cid = cat.category_id
        return [p for p in self.products if any(c.category_id == target_cid for c in p.categories)]

    def get_all(self):
        return self.products