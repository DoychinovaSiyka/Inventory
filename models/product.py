from datetime import datetime
from models.category import Category
from validators.product_validator import ProductValidator


class Product:
    def __init__(self, product_id, name, categories, quantity, unit, description, price,
                 supplier_id=None, tags=None, created=None, modified=None, location_id="W1"):

        # Просто си пълним данните
        self.product_id = str(product_id) if product_id else None
        self.name = name
        self.categories = categories if isinstance(categories, list) else []
        self.quantity = quantity
        self.price = price
        self.unit = unit if unit else "бр."
        self.description = description
        self.supplier_id = str(supplier_id) if supplier_id else None
        self.tags = tags if isinstance(tags, list) else []
        self.location_id = str(location_id)

        self.created = created or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.modified = modified or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Викаме валидатора да си свърши работата
        ProductValidator.validate_all(
            product_id=self.product_id,
            name=self.name,
            categories=self.categories,
            quantity=self.quantity,
            unit=self.unit,
            description=self.description,
            price=self.price,
            location_id=self.location_id,
            supplier_id=self.supplier_id,
            tags=self.tags
        )

    def update_modified(self):
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """Превръща обекта в речник за JSON - категориите стават чисти стрингове."""
        json_categories = []
        for c in self.categories:
            if isinstance(c, Category):
                json_categories.append(str(c.category_id))
            else:
                json_categories.append(str(c))

        return {
            "product_id": self.product_id,
            "name": self.name,
            "categories": json_categories,
            "quantity": self.quantity,
            "unit": self.unit,
            "description": self.description,
            "price": self.price,
            "supplier_id": self.supplier_id,
            "tags": self.tags,
            "location_id": self.location_id,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data, category_controller=None):
        """Прави нов Product от речник (JSON)."""
        raw_categories = data.get("categories", [])
        fixed_categories = []

        # Ако има контролер, зареждаме обектите Category
        if category_controller:
            for cid in raw_categories:
                found_cat = category_controller.get_by_id(str(cid))
                fixed_categories.append(found_cat if found_cat else str(cid))
        else:
            fixed_categories = raw_categories

        return Product(
            product_id=data.get("product_id"),
            name=data.get("name", "Неизвестен"),
            categories=fixed_categories,
            quantity=data.get("quantity", 0),
            unit=data.get("unit", "бр."),
            description=data.get("description", ""),
            price=data.get("price", 0),
            supplier_id=data.get("supplier_id"),
            tags=data.get("tags", []),
            location_id=data.get("location_id", "W1"),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        return f"{self.name} | {self.price} лв. | {self.quantity} {self.unit}"