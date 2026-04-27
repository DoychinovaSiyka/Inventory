import uuid
from datetime import datetime
from models.category import Category


class Product:
    def __init__(self, product_id, name, categories, unit, description, price,
                 supplier_id=None, tags=None, location_id=None,
                 created=None, modified=None):

        # Ако няма подадено ID – генерирам ново
        self.product_id = str(product_id) if product_id else Product.generate_id()
        self.name = name
        self.categories = categories if isinstance(categories, list) else []

        # Ако няма подадена мерна единица – използвам "бр."
        self.unit = unit if unit else "бр."

        self.description = description
        self.price = float(price)

        # Доставчик – пазя само ID-то
        self.supplier_id = str(supplier_id) if supplier_id else None

        # Тагове – ако не е списък, правя го на празен
        self.tags = tags if isinstance(tags, list) else []

        # Локация на продукта (ако има)
        self.location_id = location_id

        # Дати за създаване и промяна
        now = Product.now()
        self.created = created or now
        self.modified = modified or now

    # Генерираме ново ID за продукт
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    # Връщаме текущия момент като текст
    @staticmethod
    def now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_modified(self):
        """Обновявам датата при промяна на продукта."""
        self.modified = Product.now()

    def to_dict(self):
        """Правя обекта на речник за JSON. Категориите ги превръщам в ID-та."""
        json_categories = []
        for c in self.categories:
            if isinstance(c, Category):
                json_categories.append(str(c.category_id))
            else:
                json_categories.append(str(c))

        return {"product_id": self.product_id, "name": self.name,
                "categories": json_categories, "unit": self.unit,
                "description": self.description, "price": self.price,
                "supplier_id": self.supplier_id, "tags": self.tags,
                "location_id": self.location_id, "created": self.created,
                "modified": self.modified}

    @staticmethod
    def from_dict(data, category_controller=None):
        """Създавам Product от JSON речник. Ако има контролер – връщам Category обекти."""
        if not data:
            return None

        raw_categories = data.get("categories", [])
        fixed_categories = []

        # Ако имаме контролер – опитвам се да върна Category обекти
        if category_controller:
            for cid in raw_categories:
                if isinstance(cid, dict):
                    fixed_categories.append(Category.from_dict(cid))
                else:
                    cat = category_controller.get_by_id(str(cid))
                    if cat:
                        fixed_categories.append(cat)
        else:
            fixed_categories = []

        return Product(product_id=data.get("product_id"), name=data.get("name", "Неизвестен"),
                       categories=fixed_categories, unit=data.get("unit", "бр."),
                       description=data.get("description", ""), price=data.get("price", 0),
                       supplier_id=data.get("supplier_id"), tags=data.get("tags", []),
                       location_id=data.get("location_id"), created=data.get("created"), modified=data.get("modified"))


    def __str__(self):
        return f"{self.name} | {self.price} лв. | {self.unit}"
