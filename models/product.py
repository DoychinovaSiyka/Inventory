import uuid
from datetime import datetime
from models.category import Category


class Product:
    def __init__(self, product_id, name, categories, unit, description, price, supplier_id=None,
                 tags=None, created=None, modified=None):
        """ Моделът описва само продукта като елемент от каталога.
        Локации и количества НЕ се държат тук – те са в инвентара и движенията."""

        # Ако няма подадено ID, генерирам ново – така всеки продукт е уникален
        self.product_id = str(product_id) if product_id else str(uuid.uuid4())

        # Основни свойства
        self.name = name
        self.categories = categories if isinstance(categories, list) else []

        # Ако няма подадена мерна единица, ползвам "бр."
        self.unit = unit if unit else "бр."

        self.description = description
        self.price = float(price)

        # Доставчик – само ID-то
        self.supplier_id = str(supplier_id) if supplier_id else None

        # Тагове – ако не е списък, правя го на празен
        self.tags = tags if isinstance(tags, list) else []

        # Локация вече НЕ се пази в модела (премахнато заради парадокса)
        # self.location_id = location_id

        # Дати за създаване и промяна
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        """Обновявам датата при промяна на продукта."""
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """Правя обекта на речник за JSON. Категориите ги превръщам в ID-та."""
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
            # "location_id": self.location_id,  # Премахнато
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data, category_controller=None):
        """
        Създавам Product от JSON речник.
        Ако има контролер – връщам Category обекти.
        Ако няма – запазвам ID-тата като стрингове.
        """
        if not data:
            return None

        raw_categories = data.get("categories", [])
        fixed_categories = []

        if category_controller:
            for cid in raw_categories:
                # Ако е речник - директно създавам Category
                if isinstance(cid, dict):
                    fixed_categories.append(Category.from_dict(cid))
                else:
                    # Ако е ID - търся го в контролера
                    cat = category_controller.get_by_id(str(cid))
                    if cat:
                        fixed_categories.append(cat)
                    else:
                        # Ако категорията е изтрита – запазвам ID-то
                        fixed_categories.append(str(cid))
        else:
            # Ако няма контролер – запазвам ID-тата
            fixed_categories = [str(c) for c in raw_categories]

        return Product(
            product_id=data.get("product_id"),
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
        return f"{self.name} | {self.price:.2f} лв. | {self.unit}"
