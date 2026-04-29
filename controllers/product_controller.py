import uuid
from models.product import Product
from validators.product_validator import ProductValidator


class ProductController:
    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.activity_log_controller = activity_log_controller
        self.products = self.load()
        self.movement_controller = None


    # ЗАРЕЖДАНЕ / ЗАПИС
    def load(self):
        data = self.repo.load() or []
        return [Product.from_dict(p, self.category_controller) for p in data]

    def save_changes(self):
        data = [p.to_dict() for p in self.products]
        self.repo.save(data)

    def _generate_id(self):
        return str(uuid.uuid4())


    # СЪЗДАВАНЕ НА ПРОДУКТ
    def add(self, product_data: dict, user_id: str) -> Product:
        ProductValidator.validate_name(product_data['name'])

        # Категории - списък от Category обекти
        categories = [self.category_controller.get_by_id(cid) for cid in product_data['category_ids']]
        product = Product(product_id=self._generate_id(), name=product_data['name'], categories=categories,
                          unit=product_data['unit'], description=product_data['description'],
                          price=float(product_data['price']), supplier_id=product_data.get('supplier_id', None))

        self.products.append(product)
        self.save_changes()

        # Начално IN движение
        initial_qty = float(product_data.get("quantity", 0))
        location_id = product_data.get("location_id")

        if initial_qty > 0 and location_id and self.movement_controller:
            self.movement_controller.add(product_id=product.product_id, user_id=user_id, location_id=location_id,
                                         movement_type="IN", quantity=str(initial_qty),
                                         description="Начално зареждане при създаване на продукт", price=str(product.price))

        return product


    # ТЪРСЕНЕ
    def search(self, keyword):
        keyword = keyword.lower()
        results = []

        for p in self.products:
            name = p.name.lower()
            category_text = " ".join([c.name.lower() for c in p.categories]) if p.categories else ""
            description = p.description.lower() if p.description else ""
            supplier = str(p.supplier_id).lower() if p.supplier_id else ""
            tags = ""
            try:
                if p.tags:
                    tags = " ".join([t.lower() for t in p.tags])
            except:
                tags = ""

            if (keyword in name or keyword in category_text or keyword in description or
                    keyword in supplier or keyword in tags):
                results.append(p)

        return results



    def search_combined(self, keyword=None, min_price=None, max_price=None,
                        category_id=None, location_id=None, inventory_controller=None):

        results = []

        for p in self.products:
            if keyword:
                if keyword.lower() not in p.name.lower() and keyword.lower() not in p.description.lower():
                    continue

            if min_price is not None and p.price < min_price:
                continue
            if max_price is not None and p.price > max_price:
                continue

            if category_id:
                if not any(c.category_id == category_id for c in p.categories):
                    continue
            if location_id and inventory_controller:
                stock = inventory_controller.data["products"].get(p.product_id, {})
                loc_stock = stock.get("locations", {}).get(location_id, 0)
                if loc_stock <= 0:
                    continue

            results.append(p)
        return results


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
        if new_supplier_id is not None:
            product.supplier_id = new_supplier_id

        self.save_changes()

        return True


    def filter_by_category(self, category_id):
        """Връща всички продукти, които имат дадената категория."""
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
