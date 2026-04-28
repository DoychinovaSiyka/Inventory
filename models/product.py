import uuid
from datetime import datetime
from models.category import Category


class Product:
    def __init__(self, product_id, name, categories, unit, description, price,
                 supplier_id=None, tags=None, created=None, modified=None):
        """ Моделът описва само продукта като елемент от каталога. """

        self.product_id = str(product_id) if product_id else str(uuid.uuid4())
        self.name = name
        self.categories = categories if isinstance(categories, list) else []
        self.unit = unit
        self.description = description
        self.price = float(price)
        self.supplier_id = str(supplier_id) if supplier_id else None
        self.tags = tags if isinstance(tags, list) else []

        now = Product.now()
        self.created = created or now
        self.modified = modified or now

    @staticmethod
    def now():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_modified(self):
        self.modified = Product.now()

    def to_dict(self):
        """Правя обекта на речник за JSON. Категориите ги превръщам в ID-та."""
        json_categories = []
        for c in self.categories:
            if isinstance(c, Category):
                json_categories.append(str(c.category_id))
            else:
                json_categories.append(str(c))

        return {"product_id": self.product_id, "name": self.name, "categories": json_categories,
                "unit": self.unit, "description": self.description, "price": self.price,
                "supplier_id": self.supplier_id, "tags": self.tags,
                "created": self.created, "modified": self.modified}

    @staticmethod
    def from_dict(data, category_controller=None):
        """Създавам Product от JSON речник. Ако има контролер – връщам Category обекти.
        Ако няма – запазвам ID-тата като стрингове."""
        if not data:
            return None

        raw_categories = data.get("categories", [])
        fixed_categories = []

        if category_controller:
            for cid in raw_categories:
                if isinstance(cid, dict):
                    fixed_categories.append(Category.from_dict(cid))
                else:
                    cat = category_controller.get_by_id(str(cid))
                    fixed_categories.append(cat if cat else str(cid))
        else:
            fixed_categories = [str(c) for c in raw_categories]

        return Product(product_id=data.get("product_id"), name=data.get("name", "Неизвестен"),
                       categories=fixed_categories, unit=data.get("unit"),
                       description=data.get("description", ""), price=data.get("price", 0),
                       supplier_id=data.get("supplier_id"), tags=data.get("tags", []),
                       created=data.get("created"), modified=data.get("modified"))

    def __str__(self):
        return f"{self.name} | {self.price:.2f} лв. | {self.unit}"
