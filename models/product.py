import uuid
from datetime import datetime
from models.category import Category
from validators.product_validator import ProductValidator


class Product:
    """
    МОДЕЛ НА ПРОДУКТ
    Продуктът е чист запис: име, описание, цена, категории, доставчик, тагове
    """

    def __init__(self, product_id, name, categories, unit, description, price,
                 supplier_id=None, tags=None, created=None, modified=None):

        # ако няма подадено id → генерираме UUID
        self.product_id = str(product_id) if product_id else str(uuid.uuid4())
        self.name = name
        self.categories = categories if isinstance(categories, list) else []

        self.unit = unit if unit else "бр."
        self.description = description
        self.price = float(price)
        self.supplier_id = str(supplier_id) if supplier_id else None
        self.tags = tags if isinstance(tags, list) else []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created or now
        self.modified = modified or now

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
            "unit": self.unit,
            "description": self.description,
            "price": self.price,
            "supplier_id": self.supplier_id,
            "tags": self.tags,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data, category_controller=None):
        """Прави нов Product от речник (JSON)."""
        if not data:
            return None

        raw_categories = data.get("categories", [])
        fixed_categories = []

        if category_controller:
            for cid in raw_categories:
                cat = category_controller.get_by_id(str(cid))
                fixed_categories.append(cat if cat else str(cid))
        else:
            fixed_categories = raw_categories

        return Product(
            product_id=data.get("product_id"),  # ако липсва → ще се генерира UUID
            name=data.get("name", "Неизвестен"),
            categories=fixed_categories,
            unit=data.get("unit", "бр."),
            description=data.get("description", ""),
            price=data.get("price", 0),
            supplier_id=data.get("supplier_id"),
            tags=data.get("tags", []),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        return f"{self.name} | {self.price} лв. | {self.unit}"
