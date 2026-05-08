import uuid
from datetime import datetime


class Product:
    def __init__(self, product_id, name, categories, unit, description, price,
                 created=None, modified=None):


        if not product_id:
            self.product_id = str(uuid.uuid4())
        else:
            self.product_id = str(product_id)

        self.name = name
        self.categories = categories  # списък от Category обекти
        self.unit = unit
        self.description = description
        self.price = float(price)

        # Сетване на дати
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not created:
            self.created = now
        else:
            self.created = created

        if not modified:
            self.modified = now
        else:
            self.modified = modified

    def update_modified(self):
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_category_ids(self):
        """Връща списък от ID-тата на категориите."""
        ids_list = []
        for c in self.categories:
            # Проверяваме дали c е обект (има атрибут category_id)
            if hasattr(c, "category_id"):
                ids_list.append(str(c.category_id))
            else:
                ids_list.append(str(c))
        return ids_list

    def to_dict(self):
        """Подготвя обекта за запис в JSON файл."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "categories": self.get_category_ids(),
            "unit": self.unit,
            "description": self.description,
            "price": self.price,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data, category_controller=None):
        """Възстановява обекта от речник."""
        categories_list = []

        # Вземаме списъка с ID-та от данните
        raw_ids = data.get("categories", [])

        if category_controller:
            for cid in raw_ids:
                category_obj = category_controller.get_by_id(cid)
                if category_obj:
                    categories_list.append(category_obj)
                else:
                    # Ако не го намерим в базата, пазим само ID-то
                    categories_list.append(cid)
        else:

            categories_list = raw_ids


        desc = data.get("description", "")

        return Product(
            product_id=data.get("product_id"),
            name=data.get("name"),
            categories=categories_list,
            unit=data.get("unit"),
            description=desc,
            price=data.get("price", 0.0),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        short_id = self.product_id[:8]

        # Сглобяваме имената на категориите за принтиране
        names_list = []
        for c in self.categories:
            if hasattr(c, "name"):
                names_list.append(c.name)
            else:
                names_list.append(str(c))

        if names_list:
            cats_str = ", ".join(names_list)
        else:
            cats_str = "Няма"

        return (f"Продукт: {self.name} [ID: {short_id}]\n"
                f"  - Категории: {cats_str}\n"
                f"  - Цена: {self.price:.2f} {self.unit}")