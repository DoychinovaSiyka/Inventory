import uuid
from models.product import Product
from validators.product_validator import ProductValidator


class ProductController:
    def __init__(self, repo, category_controller, activity_log_controller=None):
        self.repo = repo
        self.category_controller = category_controller
        self.activity_log_controller = activity_log_controller
        self.products = self.load()
        self.movement_controller = None  # свързва се от main.py

    def load(self):
        data = self.repo.load() or []
        return [Product.from_dict(p, self.category_controller) for p in data]

    def save_changes(self):
        data = [p.to_dict() for p in self.products]
        self.repo.save(data)

    def _generate_id(self):
        return str(uuid.uuid4())

    def add(self, product_data: dict, user_id: str) -> Product:
        # Валидация
        ProductValidator.validate_name(product_data['name'])

        # Категории
        categories = [
            self.category_controller.get_by_id(cid)
            for cid in product_data['category_ids']
        ]

        # Създаване на продукт (БЕЗ quantity!)
        product = Product(
            product_id=self._generate_id(),
            name=product_data['name'],
            categories=categories,
            unit=product_data['unit'],
            description=product_data['description'],
            price=float(product_data['price']),
            supplier_id=product_data.get('supplier_id', None)
        )

        # Запис в products.json
        self.products.append(product)
        self.save_changes()

        # ---------------------------------------------
        #  СЪЗДАВАМЕ НАЧАЛНО IN ДВИЖЕНИЕ
        # ---------------------------------------------
        initial_qty = float(product_data.get("quantity", 0))
        location_id = product_data.get("location_id")

        if initial_qty > 0 and location_id and self.movement_controller:
            self.movement_controller.add(
                product_id=product.product_id,
                user_id=user_id,
                location_id=location_id,
                movement_type="IN",
                quantity=str(initial_qty),
                description="Начално зареждане при създаване на продукт",
                price=str(product.price)
            )

        return product

    def search_combined(self, keyword=None, min_price=None, max_price=None,
                        category_id=None, location_id=None, inventory_controller=None):

        results = []

        for p in self.products:

            # --- Ключова дума ---
            if keyword:
                if keyword.lower() not in p.name.lower() and keyword.lower() not in p.description.lower():
                    continue

            # --- Цена ---
            if min_price is not None and p.price < min_price:
                continue
            if max_price is not None and p.price > max_price:
                continue

            # --- Категория ---
            if category_id:
                if not any(c.category_id == category_id for c in p.categories):
                    continue

            # --- Локация (наличност) ---
            if location_id and inventory_controller:
                stock = inventory_controller.data["products"].get(p.product_id, {})
                loc_stock = stock.get("locations", {}).get(location_id, 0)
                if loc_stock <= 0:
                    continue

            results.append(p)

        return results

    def get_all(self):
        return self.products

    def get_by_id(self, product_id):
        product_id = str(product_id)
        for p in self.products:
            if p.product_id == product_id:
                return p
        return None
