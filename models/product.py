
import uuid
from validators.product_validator import ProductValidator
from models.category import Category

class Product:
    next_id = 1  # Статична променлива за следене на следващото ID

    def __init__(self, name, categories, quantity, description, price,
                 product_id=None, category_id=None, supplier_id=None):

        # Валидации
        ProductValidator.validate_name(name)
        ProductValidator.validate_categories(categories)
        ProductValidator.validate_quantity(quantity)
        ProductValidator.validate_description(description)
        ProductValidator.validate_price(price)

        self.product_id = product_id or Product.next_id
        Product.next_id+= 1

        self.category_id = category_id or str(uuid.uuid4())
        self.supplier_id = supplier_id or str(uuid.uuid4())

        self.name = name
        self.categories = categories
        self.quantity = quantity
        self.description  = description
        self.price = price


    @staticmethod
    def from_dict(data):  # десериализация: превръща речник в обект
        return Product(
            name=data["name"],
            categories=[Category.from_dict(c) for c in data.get("categories", [])],
            quantity=data["quantity"],
            description=data["description"],
            price=data["price"],
            product_id=data.get("product_id"),
            category_id=data.get("category_id"),
            supplier_id=data.get("supplier_id")
        )

    def to_dict(self):  # сериализация: превръща обекта обратно в речник
        return {
            "product_id": self.product_id,
            "name": self.name,
            "categories": [c.to_dict() for c in self.categories],
            "quantity": self.quantity,
            "description": self.description,
            "price": self.price,
            "category_id": self.category_id,
            "supplier_id": self.supplier_id
        }
