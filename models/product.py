import uuid
from datetime import datetime


class Product:
    def __init__(self, product_id, name, categories, unit, description, price,
                 created=None, modified=None):

        # 1. ГЕНЕРИРАНЕ: Вече пазим пълното 36-символно UUID за базата
        if not product_id:
            self.product_id = str(uuid.uuid4())
        else:
            self.product_id = str(product_id)

        self.name = name
        self.categories = categories  # Списък от обекти Category
        self.unit = unit
        self.description = description
        self.price = float(price)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created if created else now
        self.modified = modified if modified else now

    def update_modified(self):
        """Обновява датата при редакция."""
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """
        Записваме в JSON пълното ID на продукта и пълните ID-та на категориите му.
        """
        return {
            "product_id": self.product_id,
            "name": self.name,
            # Тук също пазим пълните ID-та на категориите за сигурна връзка
            "categories": [c.category_id for c in self.categories] if self.categories else [],
            "unit": self.unit,
            "description": self.description,
            "price": self.price,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data, category_controller=None):
        """Възстановява обекта и неговите връзки."""
        categories = []
        if category_controller:
            cat_ids = data.get("categories", [])
            for cid in cat_ids:
                # Контролерът вече знае как да намери категория по пълно или кратко ID
                c = category_controller.get_by_id(cid)
                if c:
                    categories.append(c)

        return Product(
            product_id=data.get("product_id"),
            name=data.get("name"),
            categories=categories,
            unit=data.get("unit"),
            description=data.get("description", ""),
            price=data.get("price", 0.0),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        # 2. ВИЗУАЛИЗАЦИЯ: Само тук режем до 8 символа за конзолата
        short_id = self.product_id[:8]
        cats_str = ", ".join([c.name for c in self.categories]) if self.categories else "Няма"

        return (f"Продукт: {self.name} [ID: {short_id}]\n"
                f"  - Категории: {cats_str}\n"
                f"  - Цена: {self.price:.2f} {self.unit}")