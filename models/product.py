import uuid
from datetime import datetime

class Product:
    def __init__(self, product_id, name, categories, unit, description, price,
                 supplier_id=None, tags=None, created=None, modified=None):

        self.product_id = str(product_id) if product_id else str(uuid.uuid4())
        self.name = name
        self.categories = categories
        self.unit = unit
        self.description = description
        self.price = float(price)
        self.supplier_id = supplier_id if supplier_id else "-"
        self.tags = tags if tags else []

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created if created else now
        self.modified = modified if modified else now

    def to_dict(self):
        return {"product_id": self.product_id, "name": self.name,
                "categories": [c.category_id for c in self.categories],
                "unit": self.unit, "description": self.description, "price": self.price,
                "supplier_id": self.supplier_id,
                "tags": self.tags, "created": self.created, "modified": self.modified}

    @staticmethod
    def from_dict(data, category_controller=None):
        categories = []
        if category_controller:
            for cid in data.get("categories", []):
                c = category_controller.get_by_id(cid)
                if c:
                    categories.append(c)

        return Product(product_id=data.get("product_id"), name=data.get("name"),
                        categories=categories, unit=data.get("unit"), description=data.get("description"),
                        price=data.get("price"), supplier_id=data.get("supplier_id"),
                        tags=data.get("tags", []), created=data.get("created"), modified=data.get("modified"))
