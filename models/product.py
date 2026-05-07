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
        self.categories = categories
        self.unit = unit
        self.description = description
        self.price = float(price)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if created:
            self.created = created
        else:
            self.created = now

        if modified:
            self.modified = modified
        else:
            self.modified = now

    def update_modified(self):
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        cat_ids = []
        if self.categories:
            for c in self.categories:
                cat_ids.append(c.category_id)

        return {
            "product_id": self.product_id,
            "name": self.name,
            "categories": cat_ids,
            "unit": self.unit,
            "description": self.description,
            "price": self.price,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data, category_controller=None):
        categories = []
        if category_controller:
            cat_ids = data.get("categories", [])
            for cid in cat_ids:
                c = category_controller.get_by_id(cid)
                if c:
                    categories.append(c)

        return Product(product_id=data.get("product_id"), name=data.get("name"), categories=categories,
                       unit=data.get("unit"), description=data.get("description", ""),
                       price=data.get("price", 0.0), created=data.get("created"), modified=data.get("modified"))

    def __str__(self):
        short_id = self.product_id[:8]

        if self.categories:
            names = []
            for c in self.categories:
                names.append(c.name)
            cats_str = ", ".join(names)
        else:
            cats_str = "Няма"

        return (f"Продукт: {self.name} [ID: {short_id}]\n"
                f"  - Категории: {cats_str}\n"
                f"  - Цена: {self.price:.2f} {self.unit}")
