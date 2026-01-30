import uuid
from datetime import datetime
from validators.product_validator import ProductValidator
from models.category import Category

class Product:
    def __init__(self, name, categories, quantity, description, price,
                 product_id=None, category_id=None, supplier_id=None, location_id=None,
                 created=None, modified=None):

        # Валидации
        ProductValidator.validate_name(name)
        ProductValidator.validate_categories(categories)
        ProductValidator.validate_quantity(quantity)
        ProductValidator.validate_description(description)
        ProductValidator.validate_price(price)

        # ID-та
        self.product_id = product_id or str(uuid.uuid4())
        self.category_id = category_id
        self.supplier_id = supplier_id
        self.location_id = location_id

        # Основни полета
        self.name = name
        self.categories = categories
        self.quantity = quantity
        self.description = description
        self.price = price

        # Дати
        self.created = created or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.modified = modified or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.validate()

    def validate(self):
        ProductValidator.validate_name(self.name)
        ProductValidator.validate_categories(self.categories)
        ProductValidator.validate_quantity(self.quantity)
        ProductValidator.validate_description(self.description)
        ProductValidator.validate_price(self.price)

    def update_modified(self):
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def increase_quantity(self, amount):
        if amount <= 0:
            raise ValueError("Увеличението трябва да е положително число.")
        self.quantity += amount
        self.update_modified()

    def decrease_quantity(self, amount):
        if amount <= 0:
            raise ValueError("Намалението трябва да е положително число.")
        if amount > self.quantity:
            raise ValueError("Няма достатъчно наличност.")
        self.quantity -= amount
        self.update_modified()

    def is_low_stock(self, threshold=5):
        return self.quantity <= threshold

    @property
    def price_with_vat(self):
        vat_rate = 0.20
        return round(self.price * (1 + vat_rate), 2)

    @staticmethod
    def from_dict(data):
        return Product(
            name=data["name"],
            categories=[Category.from_dict(c) for c in data.get("categories", [])],
            quantity=data["quantity"],
            description=data["description"],
            price=data["price"],
            product_id=data.get("product_id"),
            category_id=data.get("category_id"),
            supplier_id=data.get("supplier_id"),
            location_id=data.get("location_id"),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "categories": [c.to_dict() for c in self.categories],
            "quantity": self.quantity,
            "description": self.description,
            "price": self.price,
            "category_id": self.category_id,
            "supplier_id": self.supplier_id,
            "location_id": self.location_id,
            "created": self.created,
            "modified": self.modified
        }
