import uuid
from datetime import datetime


class Product:
    def __init__(self, product_id, name, categories, unit, description, price, created=None, modified=None):

        self.product_id = str(product_id) if product_id else str(uuid.uuid4())
        self.name = name
        self.categories = categories or []  # Списък от Category обекти или ID-та
        self.unit = unit
        self.description = description
        self.price = float(price)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    def to_dict(self):
        """Превръща обекта в речник за запис в JSON."""
        category_ids = [str(c.category_id) for c in self.categories]

        return {"product_id": self.product_id, "name": self.name, "categories": category_ids,
                 "unit": self.unit, "description": self.description,
                 "price": self.price, "created": self.created,
                 "modified": self.modified}

    @staticmethod
    def from_dict(data, category_controller=None):
        """Възстановява обект Product от речник."""
        raw_ids = data.get("categories", [])
        categories_list = []

        if category_controller:
            for cid in raw_ids:
                obj = category_controller.get_by_id(cid)
                categories_list.append(obj if obj else cid)
        else:
            categories_list = raw_ids

        return Product(product_id=data.get("product_id"), name=data.get("name"), categories=categories_list,
                       unit=data.get("unit"), description=data.get("description", ""), price=data.get("price", 0.0),
                       created=data.get("created"), modified=data.get("modified"))

    def __str__(self):
        short_id = str(self.product_id)[:8]

        category_names = [c.name for c in self.categories]
        cats = ", ".join(category_names) if category_names else "Няма"

        return (f"Продукт: {self.name} (ID: {short_id})\n" f"Категории: {cats}\n" f"Цена: {float(self.price):.2f} {self.unit}")
