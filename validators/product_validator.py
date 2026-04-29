import uuid
from models.category import Category


class ProductValidator:

    # Проверка за валиден UUID
    @staticmethod
    def validate_uuid(value, field_name="ID"):
        if value is None:
            return None
        try:
            uuid.UUID(str(value))
        except (ValueError, TypeError):
            raise ValueError(f"Невалиден формат за {field_name}: {value}")
        return value


    @staticmethod
    def validate_name(name):
        if not name or not isinstance(name, str):
            raise ValueError("Името на продукта е задължително.")
        name = name.strip()
        if len(name) < 3:
            raise ValueError("Името трябва да е поне 3 символа.")
        return name


    @staticmethod
    def validate_description(description):
        if description is None:
            raise ValueError("Описанието е задължително.")
        if not isinstance(description, str):
            raise ValueError("Описанието трябва да е текст.")
        desc = description.strip()
        if len(desc) < 3:
            raise ValueError("Описанието е твърде кратко.")
        if len(desc) > 1000:
            raise ValueError("Описанието е твърде дълго.")
        return desc


    @staticmethod
    def validate_categories(categories):
        if not isinstance(categories, list):
            raise ValueError("Категориите трябва да са списък.")
        if len(categories) == 0:
            raise ValueError("Трябва поне една категория.")

        for c in categories:
            cid = str(c.category_id) if isinstance(c, Category) else str(c)
            if not cid.strip():
                raise ValueError("Има празна или невалидна категория.")
        return categories


    @staticmethod
    def validate_quantity(quantity):
        try:
            q = float(quantity)
        except (ValueError, TypeError):
            raise ValueError("Количеството трябва да е число.")
        if q <= 0:
            raise ValueError("Количеството трябва да е над 0.")
        return round(q, 2)


    @staticmethod
    def validate_unit(unit):  # проверка и нормализиране на мерната единица
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")

        u = unit.strip().lower()
        mapping = {"кг": "кг.", "kg": "кг.", "килограм": "кг.", "килограма": "кг.",
                   "килограми": "кг.", "бр": "бр.", "бр.": "бр.", "брой": "бр.", "l": "л.",
                   "л": "л.", "литър": "л.", "литра": "л.", "литри": "л.", "пакет": "пакет",
                   "paket": "пакет", "packet": "пакет"}

        parts = u.split()
        if len(parts) > 1:
            u = parts[-1]

        if u in mapping:
            return mapping[u]

        allowed = ["кг.", "бр.", "л.", "пакет"]
        if u not in allowed:
            raise ValueError(f"Невалидна мерна единица. Разрешени: {', '.join(allowed)}")
        return u


    @staticmethod
    def validate_price(price):
        try:
            p = float(price)
        except (ValueError, TypeError):
            raise ValueError("Цената трябва да е число.")
        if p <= 0:
            raise ValueError("Цената трябва да е над 0.")
        return round(p, 2)


    # Помощни парсери
    @staticmethod
    def _parse_float_internal(value, field_name="стойност"):  # чистя лв., запетаи и т.н.
        if isinstance(value, str):
            value = (value.replace("лв.", "").replace("лв", "").replace("lv.", "")
                     .replace("lv", "").replace("BGN", "").replace("bgn", "").replace(",", ".").strip())
        try:
            f = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} трябва да е число.")
        return round(f, 2)


    @staticmethod
    def parse_float(value, field_name="стойност"):
        f = ProductValidator._parse_float_internal(value, field_name)
        if f <= 0:
            raise ValueError(f"{field_name} трябва да е над 0.")
        return f


    @staticmethod
    def parse_int(value, field_name="стойност"):
        if value is None or str(value).strip() == "":
            raise ValueError(f"{field_name} е задължително.")
        try:
            i = int(str(value).strip())
        except ValueError:
            raise ValueError(f"{field_name} трябва да е цяло число.")
        if i < 0:
            raise ValueError(f"{field_name} не може да е отрицателно.")
        return i


    @staticmethod
    def parse_optional_float(value: str | None):
        """Парсира число, приема '10', '10.5', '10,5', '10 лв', '10лв', връща None при празен вход."""
        if value is None:
            return None

        value = value.strip()
        if value == "":
            return None

        # Почистване на валутни символи и текст
        cleaned = (value.replace("лв.", "")
                         .replace("лв", "")
                         .replace("lv.", "")
                         .replace("lv", "")
                         .replace("BGN", "")
                         .replace("bgn", "")
                         .replace(",", ".")
                         .strip())

        try:
            return float(cleaned)
        except ValueError:
            raise ValueError("Моля, въведете валидно число.")


    @staticmethod
    def validate_product_exists(product_id, product_controller):  # продуктът трябва да съществува
        product = product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")
        return product


    @staticmethod
    def validate_category_exists(category_ids, category_controller):  # проверка за категории
        for cid in category_ids:
            if not category_controller.get_by_id(cid):
                raise ValueError(f"Категория с ID {cid} не съществува.")


    @staticmethod
    def validate_supplier_exists(supplier_id, supplier_controller):  # доставчик – ако има, трябва да е валиден
        if supplier_id is None:
            return
        supplier = supplier_controller.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")


    # Проверка за дублиране в склад
    @staticmethod
    def validate_unique_name_in_location(name, location_id, products):  # име + склад → уникално
        for p in products:
            if p.name.lower() == name.lower() and getattr(p, "location_id", None) == location_id:
                raise ValueError("Продуктът вече съществува в този склад.")


    # Проверка за уникално име в целия каталог
    @staticmethod
    def validate_unique_name(name, products, exclude_product_id=None):
        """Проверява дали името вече съществува в глобалния каталог."""
        if not name:
            return

        name_lower = name.strip().lower()
        for p in products:
            # Ако редактираме, пропускаме текущия продукт
            if exclude_product_id is not None and str(p.product_id) == str(exclude_product_id):
                continue
            if p.name.lower() == name_lower:
                raise ValueError(f"Продукт с име '{name}' вече съществува в каталога.")
        return True
