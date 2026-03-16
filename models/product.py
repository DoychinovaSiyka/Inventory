from datetime import datetime
from uuid import UUID
from models.category import Category

def validate_uuid(value):
    if value is None:
        return None
    try:
        return str(UUID(str(value)))
    except ValueError:
        raise ValueError(f"Invalid UUID value: {value}")

class Product:
    def __init__(self, product_id, name, categories, quantity, unit, description, price,
                 supplier_id=None, tags=None, created=None, modified=None):

        self.product_id = validate_uuid(product_id)
        self.name = name

        # преобразуваме категориите в UUID низове
        self.categories = [validate_uuid(c.category_id) if isinstance(c, Category) else validate_uuid(c)
            for c in categories]

        self.quantity = float(quantity)
        self.unit = unit
        self.description = description
        self.price = float(price)

        self.supplier_id = validate_uuid(supplier_id)
        self.tags = tags or []

        self.created = created or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.modified = modified or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_modified(self):
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        return f"{self.name} | {self.price:.2f} лв. | {self.quantity} {self.unit}"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,

            # Ако е Category - взимаме category_id
            # Ако е UUID - връщаме директно
            "categories": [
                c.category_id if isinstance(c, Category) else c
                for c in self.categories
            ],

            "quantity": self.quantity,
            "unit": self.unit,
            "description": self.description,
            "price": self.price,
            "supplier_id": self.supplier_id,
            "tags": self.tags,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        return Product(product_id=data["product_id"],
            name=data["name"],
            categories=data["categories"],
            quantity=data["quantity"],
            unit=data.get("unit", "бр."),
            description=data["description"],
            price=data["price"],
            supplier_id=data.get("supplier_id"),
            tags=data.get("tags", []),created=data.get("created"),modified=data.get("modified"))
