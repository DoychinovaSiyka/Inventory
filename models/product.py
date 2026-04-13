from datetime import datetime
import uuid
from models.category import Category
from validators.product_validator import ProductValidator


def validate_uuid(value):
    """Връща валиден UUID като string или None. Хвърля грешка при невалиден формат."""
    if value is None:
        return None
    uuid.UUID(str(value))  # ще хвърли грешка ако е невалиден
    return str(value)


class Product:
    def __init__(self, product_id, name, categories, quantity, unit, description, price,
                 supplier_id=None, tags=None, created=None, modified=None, location_id="W1"):

        self.product_id = validate_uuid(product_id)
        self.name = name

        # КАТЕГОРИИ (винаги списък от стрингове)
        self.categories = []
        if isinstance(categories, list):
            for c in categories:
                if isinstance(c, Category):
                    # Category обект - взимам category_id като string
                    self.categories.append(str(c.category_id))
                elif isinstance(c, dict):
                    # dict - взимам category_id
                    self.categories.append(str(c.get("category_id")))
                else:
                    # string - директно добавям
                    self.categories.append(str(c))

        # КОЛИЧЕСТВО И ЦЕНА (само съхранение, без валидация)
        self.quantity = quantity
        self.price = price
        self.unit = unit if unit else "бр."
        self.description = description
        self.supplier_id = validate_uuid(supplier_id)
        self.tags = tags if isinstance(tags, list) else []
        self.location_id = str(location_id)
        self.created = created or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.modified = modified or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ВАЛИДАЦИЯ
        ProductValidator.validate_all(name=self.name,
                                      categories=self.categories,
                                      quantity=self.quantity,
                                      unit=self.unit, description=self.description,
                                      price=self.price, location_id=self.location_id,
                                      supplier_id=self.supplier_id, tags=self.tags)


    def is_in_category(self, search_category_id, category_controller):
        """Проверява дали продуктът е в дадена категория или нейните подкатегории."""
        search_id = str(search_category_id)
        if search_id in self.categories:
            return True

        for my_cat_id in self.categories:
            cat_obj = category_controller.get_by_id(my_cat_id)
            if cat_obj and str(cat_obj.parent_id) == search_id:
                return True
        return False

    def update_modified(self):
        """Обновява датата на последна промяна."""
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        return f"{self.name} | {self.price} лв. | {self.quantity} {self.unit} | Склад: {self.location_id}"

    def to_dict(self):
        """Финално почистване на данните точно преди запис в JSON."""
        return {
            "product_id": str(self.product_id),
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
        """Безопасно зареждане на данни от JSON."""
        return Product(
            product_id=data.get("product_id"),
            name=data.get("name", "Неизвестен"),
            categories=data.get("categories", []),
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
