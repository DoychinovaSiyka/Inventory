import uuid
from models.category import Category


class ProductValidator:

    @staticmethod
    def validate_uuid(value, field_name="ID"):
        """Синхронизирано с кратките ID-та (8 символа)"""
        if not value:
            return None
        val_str = str(value).strip()
        # Позволяваме или пълен UUID, или нашите кратки 8-символни кодове
        if len(val_str) != 8 and len(val_str) < 32:
            raise ValueError(f"Невалиден формат за {field_name}. Очаква се кратък код (8 симв.)")
        return val_str

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
        """Направено незадължително, за да съвпада с ProductMenuView"""
        if description is None or description.strip() == "":
            return ""  # Връщаме празен низ вместо грешка

        desc = description.strip()
        if 0 < len(desc) < 3:
            raise ValueError("Описанието трябва да е поне 3 символа или празно.")
        if len(desc) > 1000:
            raise ValueError("Описанието е твърде дълго (макс 1000 симв.).")
        return desc

    @staticmethod
    def validate_unit(unit):
        """Синхронизирано форматиране на мерни единици"""
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")

        u = unit.strip().lower()
        # Разширен речник за автоматично коригиране
        mapping = {
            "кг": "кг.", "kg": "кг.", "килограм": "кг.",
            "бр": "бр.", "брой": "бр.", "pcs": "бр.",
            "л": "л.", "l": "л.", "литър": "л.",
            "пакет": "пакет", "пк": "пакет"
        }

        # Ако потребителят въведе "5 кг", взимаме само "кг"
        u = u.split()[-1]

        if u in mapping:
            return mapping[u]

        allowed = ["кг.", "бр.", "л.", "пакет"]
        if u not in allowed:
            # Ако не е в списъка, но е нормална дума, я оставяме (напр. "кутия")
            # или хвърляме грешка за пълна строгост:
            raise ValueError(f"Невалидна мерна единица. Използвайте: {', '.join(allowed)}")
        return u

    @staticmethod
    def parse_float(value, field_name="стойност"):
        """Почиства 'лв.', ',' и други символи - ползва се от MenuView"""
        if value is None or str(value).strip() == "":
            raise ValueError(f"{field_name} е задължителна.")

        if isinstance(value, str):
            value = (value.replace("лв.", "").replace("лв", "")
                     .replace(",", ".").replace("BGN", "").strip())
        try:
            f = float(value)
            if f <= 0:
                raise ValueError(f"{field_name} трябва да е положително число.")
            return round(f, 2)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} трябва да е валидно число.")

    @staticmethod
    def validate_unique_name(name, products, exclude_product_id=None):
        """Проверява за дублиращи се имена в каталога"""
        if not name: return

        name_lower = name.strip().lower()
        for p in products:
            if exclude_product_id and str(p.product_id) == str(exclude_product_id):
                continue
            if p.name.lower() == name_lower:
                raise ValueError(f"Продукт с име '{name}' вече съществува.")
        return True