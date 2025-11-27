from models.category import Category
import uuid

class Product:
    next_id = 1  # Статична променлива за следене на следващото ID

    def __init__(self, name, categories, quantity, description, price,
                 product_id=None, category_id=None, supplier_id=None):
        if product_id is not None:
            self.product_id = product_id
        else:
            self.product_id = Product.next_id
            Product.next_id += 1

        self.category_id = category_id or str(uuid.uuid4())
        self.supplier_id = supplier_id or str(uuid.uuid4())

        self.name = name
        self.categories = categories
        self.quantity = quantity
        if len(description) > 255:
            raise ValueError("Описанието не може да бъде повече от 255 символа.")
        self.description = description
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
