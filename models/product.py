import uuid
from datetime import datetime


class Product:
    def __init__(self, product_id, name, categories, unit, description, price,
                 created=None, modified=None):

        if not product_id:
            self.product_id = str(uuid.uuid4())
        else:
            self.product_id = str(product_id)

        self.name = name
        self.categories = categories  # списък от Category обекти
        self.unit = unit
        self.description = description
        self.price = float(price)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_category_ids(self):
        return [str(c.category_id) for c in self.categories]

    def to_dict(self):
        return {"product_id": self.product_id, "name": self.name, "categories": self.get_category_ids(),
                "unit": self.unit, "description": self.description, "price": self.price,
                "created": self.created, "modified": self.modified}

    @staticmethod
    def from_dict(data, category_controller=None):
        categories = []
        if category_controller:
            for cid in data.get("categories", []):
                c = category_controller.get_by_id(cid)
                if c:
                    categories.append(c)

        return Product(product_id=data.get("product_id"), name=data.get("name"), categories=categories,
                       unit=data.get("unit"), description=data.get("description", ""),
                       price=data.get("price", 0.0), created=data.get("created"), modified=data.get("modified"))

    def __str__(self):
        short_id = self.product_id[:8]
        cats_str = ", ".join([c.name for c in self.categories]) if self.categories else "Няма"

        return (f"Продукт: {self.name} [ID: {short_id}]\n"
                f"  - Категории: {cats_str}\n"
                f"  - Цена: {self.price:.2f} {self.unit}")
