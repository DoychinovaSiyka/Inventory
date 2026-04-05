from datetime import datetime
import uuid
from models.category import Category


def validate_uuid(value):
    """Валидира и превръща стойността в стринг. Справя се с UUID обекти и None."""
    if value is None:
        return None
    try:
        return str(value)
    except:
        return str(value)


class Product:
    def __init__(self, product_id, name, categories, quantity, unit, description, price,
                 supplier_id=None, tags=None, created=None, modified=None, location_id="W1"):

        # ОСНОВНА ИДЕНТИФИКАЦИЯ
        self.product_id = validate_uuid(product_id)
        self.name = name
        # КАТЕГОРИИ (винаги списък от стрингове)
        self.categories = []
        if isinstance(categories, list):
            for c in categories:
                if isinstance(c, Category):
                    self.categories.append(validate_uuid(c.category_id))
                elif isinstance(c, dict):
                    self.categories.append(validate_uuid(c.get("category_id")))
                else:
                    self.categories.append(validate_uuid(c))

        # Премахваме празни записи (None)
        self.categories = [c for c in self.categories if c is not None]

        # КОЛИЧЕСТВО И ЦЕНА
        try:
            self.quantity = round(float(quantity), 2)
        except (ValueError, TypeError):
            self.quantity = 0.0

        try:
            self.price = round(float(price), 2)
        except (ValueError, TypeError):
            self.price = 0.0

        # ДРУГИ ПОЛЕТА
        self.unit = unit if unit else "бр."
        self.description = description
        self.supplier_id = validate_uuid(supplier_id)
        self.tags = tags if isinstance(tags, list) else []
        self.location_id = str(location_id)

        # ДАТИ
        self.created = created or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.modified = modified or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
        return f"{self.name} | {self.price:.2f} лв. | {self.quantity} {self.unit} | Склад: {self.location_id}"

    def to_dict(self):
        """Финално почистване на данните точно преди запис в JSON."""
        final_categories = []
        for c in self.categories:
            if hasattr(c, 'category_id'):
                final_categories.append(str(c.category_id))
            else:
                final_categories.append(str(c))

        return {
            "product_id": str(self.product_id),
            "name": self.name,
            "categories": final_categories,
            "quantity": self.quantity,
            "unit": self.unit,
            "description": self.description,
            "price": self.price,
            "supplier_id": str(self.supplier_id) if self.supplier_id else None,
            "tags": self.tags,
            "location_id": self.location_id,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        """Безопасно зареждане на данни от JSON."""
        return Product(product_id=data.get("product_id"), name=data.get("name", "Неизвестен"), categories=data.get("categories", []),
            quantity=data.get("quantity", 0), unit=data.get("unit", "бр."), description=data.get("description", ""),
            price=data.get("price", 0), supplier_id=data.get("supplier_id"), tags=data.get("tags", []),
            location_id=data.get("location_id", "W1"), created=data.get("created"), modified=data.get("modified"))
