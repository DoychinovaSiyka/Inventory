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
        return str(uuid.uuid4())

    # СЪЗДАВАНЕ НА ПРОДУКТ
    def add(self, product_data: dict, user_id: str) -> Product:
        ProductValidator.validate_name(product_data['name'])

        categories = []
        for cid in product_data['category_ids']:
            categories.append(self.category_controller.get_by_id(cid))

        product = Product(product_id=self._generate_id(), name=product_data['name'],
                          categories=categories, unit=product_data['unit'],
                          description=product_data['description'], price=float(product_data['price']))

        self.products.append(product)
        self.save_changes()
        return product

    # ИЗТРИВАНЕ
    def delete_by_id(self, product_id, user_id=None):
        product_id = str(product_id)
        product_to_delete = None

        for p in self.products:
            if p.product_id == product_id:
                product_to_delete = p
                break

        if not product_to_delete:
            raise ValueError("Продуктът не е намерен.")

        self.products.remove(product_to_delete)
        self.save_changes()
        return True

    # ТЪРСЕНЕ
    def search(self, keyword):
        keyword = keyword.lower()
        results = []

        for p in self.products:
            name = p.name.lower()
            category_text = " ".join([c.name.lower() for c in p.categories])
            description = p.description.lower() if p.description else ""

            if keyword in name or keyword in category_text or keyword in description:
                results.append(p)

        return results

    # РАЗШИРЕНО ТЪРСЕНЕ
    def search_combined(self, keyword=None, min_price=None, max_price=None,
                        category_id=None, location_id=None, inventory_controller=None):

        results = []
        for product in self.products:
            if keyword:
                text = keyword.lower()
                if text not in product.name.lower() and text not in product.description.lower():
                    continue

            if min_price is not None and product.price < min_price:
                continue
            if max_price is not None and product.price > max_price:
                continue

            # Категория
            if category_id:
                found = False
                for cat in product.categories:
                    if cat.category_id == category_id:
                        found = True
                        break
                if not found:
                    continue

            results.append(product)

        return results

    # ОБНОВЯВАНЕ
    def update_product(self, product_id, new_name=None, new_description=None,
                       new_price=None, new_supplier_id=None, user_id=None):

        product = self.get_by_id(product_id)
        if not product:
            return False

        if new_name is not None:
            ProductValidator.validate_name(new_name)
            product.name = new_name

        if new_description is not None:
            product.description = new_description

        if new_price is not None:
            try:
                product.price = float(new_price)
            except:
                return False

        self.save_changes()
        return True


    # ФИЛТЪР ПО КАТЕГОРИЯ
    def filter_by_category(self, category_id):
        results = []
        for p in self.products:
            for c in p.categories:
                if c.category_id == category_id:
                    results.append(p)
                    break
        return results

    def get_all(self):
        return self.products

    def get_by_id(self, product_id):
        product_id = str(product_id)
        for p in self.products:
            if p.product_id == product_id:
                return p
        return None
