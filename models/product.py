from datetime import datetime
from models.category import Category

class Product:
    def __init__(
        self,
        product_id,
        name,
        categories,
        quantity,
        unit,               # ← НОВО: мерна единица
        description,
        price,
        supplier=None,
        tags=None,
        created=None,
        modified=None
    ):
        # ВАЖНО:
        # НЕ валидираме категории тук!
        # Защото при from_dict() те са UUID (стрингове),
        # а при add() ProductController ги валидира и превръща в Category обекти.

        self.product_id = product_id
        self.name = name
        self.categories = categories  # може да са UUID или Category обекти

        # Количеството вече е float
        self.quantity = float(quantity)

        # НОВО: мерна единица
        self.unit = unit

        self.description = description
        self.price = price
        self.supplier = supplier
        self.tags = tags or []
        self.created = created or str(datetime.now())
        self.modified = modified or str(datetime.now())

    def update_modified(self):
        self.modified = str(datetime.now())

    def __str__(self):
        # НОВО: показваме quantity + unit
        return f"{self.name} | {self.price:.2f} лв. | {self.quantity} {self.unit}"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "categories": [
                c.category_id if isinstance(c, Category) else c
                for c in self.categories
            ],
            "quantity": self.quantity,
            "unit": self.unit,  # ← НОВО
            "description": self.description,
            "price": self.price,
            "supplier": self.supplier.supplier_id if self.supplier else None,
            "tags": self.tags,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        # Категориите в JSON са UUID стрингове.
        # ProductController ще ги превърне в Category обекти при зареждане.
        return Product(
            product_id=data["product_id"],
            name=data["name"],
            categories=data["categories"],  # ← оставяме ги като UUID
            quantity=data["quantity"],
            unit=data.get("unit", "бр."),  # ← НОВО: ако липсва, по подразбиране "бр."
            description=data["description"],
            price=data["price"],
            supplier=data.get("supplier"),
            tags=data.get("tags", []),
            created=data.get("created"),
            modified=data.get("modified")
        )
