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
                 supplier_id=None, tags=None, created=None, modified=None, location_id="W1"):

        self.product_id = validate_uuid(product_id)
        self.name = name

        # Пазим списък от ID-та на категориите
        self.categories = [validate_uuid(c.category_id) if isinstance(c, Category) else validate_uuid(c)
                           for c in categories]

        self.quantity = float(quantity)
        self.unit = unit
        self.description = description
        self.price = float(price)

        self.supplier_id = validate_uuid(supplier_id)
        self.tags = tags or []
        self.location_id = location_id

        self.created = created or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.modified = modified or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def is_in_category(self, search_category_id, category_controller):
        """
        Проверява дали продуктът принадлежи към дадена категория
        ИЛИ към някоя от нейните подкатегории.
        """
        search_category_id = str(search_category_id)

        # 1. Директна проверка: Дали търсеното ID е в списъка на продукта
        if search_category_id in self.categories:
            return True

        # 2. Йерархична проверка: Проверяваме дали родителят на категорията на продукта
        # съвпада с търсената категория
        for my_cat_id in self.categories:
            cat_obj = category_controller.get_by_id(my_cat_id)
            if cat_obj and str(cat_obj.parent_id) == search_category_id:
                return True

        return False

    def update_modified(self):
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        return f"{self.name} | {self.price:.2f} лв. | {self.quantity} {self.unit} | Склад: {self.location_id}"

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "categories": self.categories,
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
    def from_dict(data):
        return Product(
            product_id=data["product_id"],
            name=data["name"],
            categories=data["categories"],
            quantity=data["quantity"],
            unit=data.get("unit", "бр."),
            description=data["description"],
            price=data["price"],
            supplier_id=data.get("supplier_id"),
            tags=data.get("tags", []),
            location_id=data.get("location_id", "W1"),
            created=data.get("created"),
            modified=data.get("modified")
        )