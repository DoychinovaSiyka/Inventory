from models.product import Product
from validators.product_validator import ProductValidator

class ProductController:
    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.activity_log_controller = activity_log_controller

        data = self.repo.load() or []
        self.products = [Product.from_dict(p, self.category_controller) for p in data]

    def save_changes(self):
        data = [p.to_dict() for p in self.products]
        self.repo.save(data)

    # ПРЕМАХНАТО: _generate_id вече не ни трябва тук!

    def _log(self, user_id, action, message):
        if self.activity_log_controller and user_id:
            # СИНХРОНИЗАЦИЯ: Увери се, че методът в ActivityLogController се казва лог_action или лог_event
            self.activity_log_controller.log_action(user_id, action, message)

    def add(self, product_data: dict, user_id: str) -> Product:
        ProductValidator.validate_name(product_data['name'])

        categories = []
        for cid in product_data.get('category_ids', []):
            cat = self.category_controller.get_by_id(cid)
            if cat:
                categories.append(cat)

        # СИНХРОНИЗАЦИЯ: Подаваме product_id=None, за да се задейства автоматичното 8-символно ID в модела
        product = Product(
            product_id=None,
            name=product_data['name'],
            categories=categories,
            unit=product_data.get('unit', 'бр.'),
            description=product_data.get('description', ''),
            price=float(product_data['price'])
        )

        self.products.append(product)
        self.save_changes()

        self._log(user_id, "CREATE_PRODUCT", f"Продукт: {product.name} ({product.product_id})")
        return product

    def delete_by_id(self, product_id, user_id):
        product = self.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не е намерен.")

        name_tmp = product.name
        self.products.remove(product)
        self.save_changes()

        self._log(user_id, "DELETE_PRODUCT", f"Продукт: {name_tmp} (ID: {product_id})")
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
            product.update_modified() # Добра практика е да обновяваме датата при редакция

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
            self._log(user_id, "UPDATE_PRODUCT", f"Редакция {product_id}: " + ", ".join(changes))
        return True

    def search(self, keyword):
        if not keyword:
            return self.products
        keyword = keyword.lower()
        return [p for p in self.products if keyword in p.name.lower() or
                keyword in (p.description or "").lower()]

    def filter_by_category(self, category_id):
        return [p for p in self.products if any(c.category_id == category_id for c in p.categories)]

    def get_all(self):
        return self.products

    def get_by_id(self, product_id):
        pid_str = str(product_id)
        for p in self.products:
            if p.product_id == pid_str:
                return p
        return None