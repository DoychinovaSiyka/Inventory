import uuid
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

    def _generate_id(self):
        return str(uuid.uuid4())[:8]  # По-кратки ID-та за по-лесна работа на оператора

    def _log(self, user_id, action, message):
        """Помощна функция за синхронизация с отчетите за активност"""
        if self.activity_log_controller:
            self.activity_log_controller.log_event(user_id, action, message)

    # СЪЗДАВАНЕ НА ПРОДУКТ
    def add(self, product_data: dict, user_id: str) -> Product:
        ProductValidator.validate_name(product_data['name'])

        categories = []
        for cid in product_data.get('category_ids', []):
            cat = self.category_controller.get_by_id(cid)
            if cat:
                categories.append(cat)

        product = Product(
            product_id=self._generate_id(),
            name=product_data['name'],
            categories=categories,
            unit=product_data.get('unit', 'бр.'),
            description=product_data.get('description', ''),
            price=float(product_data['price'])
        )

        self.products.append(product)
        self.save_changes()

        # ЛОГИРАНЕ: Важно за ReportsView
        self._log(user_id, "CREATE_PRODUCT", f"Създаден продукт: {product.name} (ID: {product.product_id})")

        return product

    # ИЗТРИВАНЕ
    def delete_by_id(self, product_id, user_id):
        product = self.get_by_id(product_id)
        if not product:
            raise ValueError("Продуктът не е намерен.")

        product_name = product.name
        self.products.remove(product)
        self.save_changes()

        # ЛОГИРАНЕ
        self._log(user_id, "DELETE_PRODUCT", f"Изтрит продукт: {product_name} (ID: {product_id})")
        return True

    # ОБНОВЯВАНЕ (SYNC FIX)
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

        if new_description is not None:
            product.description = new_description

        if new_price is not None:
            old_price = product.price
            product.price = float(new_price)
            changes.append(f"цена: {old_price} -> {new_price}")

        if changes:
            self.save_changes()
            # ЛОГИРАНЕ: Кой какво точно е променил
            self._log(user_id, "UPDATE_PRODUCT", f"Редакция на {product_id}: " + ", ".join(changes))

        return True

    # ТЪРСЕНЕ И ФИЛТРИ
    def search(self, keyword):
        if not keyword: return self.products
        keyword = keyword.lower()
        return [p for p in self.products if keyword in p.name.lower() or
                keyword in (p.description or "").lower()]

    def search_combined(self, keyword=None, min_price=None, max_price=None,
                        category_id=None, inventory_controller=None):
        results = self.products

        if keyword:
            results = [p for p in results if keyword.lower() in p.name.lower()]

        if min_price is not None:
            results = [p for p in results if p.price >= min_price]

        if max_price is not None:
            results = [p for p in results if p.price <= max_price]

        if category_id:
            results = [p for p in results if any(c.category_id == category_id for c in p.categories)]

        return results

    def filter_by_category(self, category_id):
        return [p for p in self.products if any(c.category_id == category_id for c in p.categories)]

    def get_all(self):
        return self.products

    def get_by_id(self, product_id):
        product_id = str(product_id)
        for p in self.products:
            if p.product_id == product_id:
                return p
        return None
