import uuid
from models.category import Category


class ProductValidator:

    # BASIC FIELD VALIDATION
    @staticmethod
    def validate_uuid(value, field_name="ID"):
        if value is None:
            return None
        try:
            uuid.UUID(str(value))
        except (ValueError, TypeError):
            raise ValueError(f"Невалиден формат за {field_name}: {value}")

    @staticmethod
    def validate_name(name):
        if not name or not isinstance(name, str):
            raise ValueError("Името на продукта е задължително.")
        name = name.strip()
        if len(name) < 3:
            raise ValueError("Името на продукта трябва да съдържа поне 3 символа.")
        return name

    @staticmethod
    def validate_description(description):
        if description is None:
            raise ValueError("Описанието е задължително.")
        if not isinstance(description, str):
            raise ValueError("Описанието трябва да бъде текстово поле.")
        desc = description.strip()
        if len(desc) < 3:
            raise ValueError("Описанието трябва да съдържа поне 3 символа.")
        if len(desc) > 1000:
            raise ValueError("Описанието не може да надвишава 1000 символа.")
        return desc

    @staticmethod
    def validate_categories(categories):
        if not isinstance(categories, list):
            raise ValueError("Категориите трябва да са списък.")
        if len(categories) == 0:
            raise ValueError("Продуктът трябва да има поне една категория.")
        for c in categories:
            cid = str(c.category_id) if isinstance(c, Category) else str(c)
            if not cid or cid.strip() == "":
                raise ValueError("Списъкът съдържа невалидна или празна категория.")
        return categories

    @staticmethod
    def validate_quantity(quantity):
        """Използва се само при създаване на продукт (начално количество)."""
        try:
            q = float(quantity)
        except (ValueError, TypeError):
            raise ValueError("Количеството трябва да е число.")

        if q <= 0:
            raise ValueError("Количеството трябва да е по-голямо от 0.")

        return round(q, 2)

    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")

        u = unit.strip().lower()
        mapping = {
            "кг": "кг.",
            "kg": "кг.",
            "килограм": "кг.",
            "килограма": "кг.",
            "килограми": "кг.",
            "бр": "бр.",
            "бр.": "бр.",
            "брой": "бр.",
            "l": "л.",
            "л": "л.",
            "литър": "л.",
            "литра": "л.",
            "литри": "л.",
            "пакет": "пакет",
            "paket": "пакет",
            "packet": "пакет"
        }

        # Премахваме числа, ако потребителят е написал "20 кг"
        parts = u.split()
        if len(parts) > 1:
            # взимаме последната дума като мерна единица
            u = parts[-1]

        # Нормализиране
        if u in mapping:
            return mapping[u]

        # Разрешени единици
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
            raise ValueError("Цената трябва да е по-голяма от 0.")

        return round(p, 2)

    # PARSING HELPERS
    @staticmethod
    def _parse_float_internal(value, field_name="стойност"):
        if isinstance(value, str):
            value = value.replace("лв.", "").replace("лв", "").strip()
            value = value.replace("lv.", "").replace("lv", "").strip()
            value = value.replace("BGN", "").replace("bgn", "").strip()
            value = value.replace(",", ".").strip()
        try:
            f = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} трябва да е число.")
        return round(f, 2)

    @staticmethod
    def parse_float(value, field_name="стойност"):
        f = ProductValidator._parse_float_internal(value, field_name)
        if f <= 0:
            raise ValueError(f"{field_name} трябва да е по-голямо от 0.")
        return f

    @staticmethod
    def parse_optional_float(value, field_name="стойност"):
        if value is None or str(value).strip() == "":
            return None
        f = ProductValidator._parse_float_internal(value, field_name)
        if f <= 0:
            raise ValueError(f"{field_name} трябва да е по-голямо от 0.")
        return f

    @staticmethod
    def parse_int(value, field_name="стойност"):
        if value is None or str(value).strip() == "":
            raise ValueError(f"{field_name} е задължително поле.")
        try:
            i = int(str(value).strip())
        except ValueError:
            raise ValueError(f"{field_name} трябва да е цяло число.")
        if i < 0:
            raise ValueError(f"{field_name} не може да е отрицателно.")
        return i

    # EXISTENCE VALIDATION
    @staticmethod
    def validate_product_exists(product_id, product_controller):
        product = product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")
        return product

    @staticmethod
    def validate_category_exists(category_ids, category_controller):
        for cid in category_ids:
            if not category_controller.get_by_id(cid):
                raise ValueError(f"Категория с ID {cid} не съществува.")

    @staticmethod
    def validate_supplier_exists(supplier_id, supplier_controller):
        if supplier_id is None:
            return
        supplier = supplier_controller.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")

    # BUSINESS RULES
    @staticmethod
    def validate_unique_name_in_location(name, location_id, products):
        for p in products:
            if p.name.lower() == name.lower() and p.location_id == location_id:
                raise ValueError("Продуктът вече съществува в този склад.")
