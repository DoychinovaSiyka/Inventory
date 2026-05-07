import uuid
from models.category import Category


class ProductValidator:

    @staticmethod
    def validate_uuid(value, field_name="ID"):
        if value is None:
            return None

        val_str = str(value).strip()
        if len(val_str) == 8:
            if not val_str.isalnum():
                raise ValueError(f"{field_name} (кратък код) съдържа невалидни символи.")
            return val_str

        if len(val_str) >= 32:
            try:
                if "-" in val_str:
                    uuid.UUID(val_str)
                return val_str
            except:
                raise ValueError(f"Невалиден UUID формат за {field_name}.")

        raise ValueError(f"Невалиден формат за {field_name}. Въведете кратък код (8 символа) или пълен UUID.")

    @staticmethod
    def validate_name(name):
        if not name or not isinstance(name, str):
            raise ValueError("Името на продукта е задължително.")

        name = name.strip()
        if len(name) < 3:
            raise ValueError("Името трябва да е поне 3 символа.")
        if len(name) > 100:
            raise ValueError("Името е твърде дълго (максимум 100 символа).")
        return name

    @staticmethod
    def validate_description(description):
        """Опционално поле — ако е празно, връща празен стринг."""
        if description is None or str(description).strip() == "":
            return ""

        desc = str(description).strip()
        if 0 < len(desc) < 3:
            raise ValueError("Описанието трябва да е поне 3 символа или да остане празно.")
        if len(desc) > 1000:
            raise ValueError("Описанието е твърде дълго.")
        return desc

    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")

        u = unit.strip().lower()

        mapping = {
            "кг": "кг.", "kg": "кг.", "килограм": "кг.", "кило": "кг.",
            "бр": "бр.", "брой": "бр.", "pcs": "бр.", "бройка": "бр.",
            "л": "л.", "l": "л.", "литър": "л.",
            "пакет": "пакет", "пк": "пакет", "pack": "пакет",
            "м": "м.", "m": "м.", "метър": "м."
        }

        u_parts = u.split()
        target_unit = u_parts[-1]

        if target_unit in mapping:
            return mapping[target_unit]

        allowed = ["кг.", "бр.", "л.", "пакет", "м.", "кв.м."]
        if target_unit not in allowed:
            if target_unit.isalpha() and len(target_unit) >= 1:
                return target_unit
            raise ValueError(f"Невалидна мерна единица. Използвайте стандартните: {', '.join(allowed)}")

        return target_unit

    @staticmethod
    def parse_float(value, field_name="стойност"):
        """Почистване и валидиране на числови стойности."""
        if value is None or str(value).strip() == "":
            raise ValueError(f"Полето '{field_name}' е задължително.")

        if isinstance(value, str):
            value = (value.replace("лв.", "").replace("лв", "")
                     .replace(",", ".").replace("bgn", "")
                     .replace(" ", "").strip())
        try:
            f = float(value)
            if f <= 0:
                raise ValueError(f"{field_name} трябва да е положително число.")
            return round(f, 2)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} трябва да бъде валидно число.")

    @staticmethod
    def validate_unique_name(name, products, exclude_product_id=None):
        """Проверява дали името на продукта вече съществува."""
        if not name:
            return

        new_name = name.strip().lower()
        for p in products:

            if exclude_product_id:
                p_id_str = str(p.product_id)
                if p_id_str == str(exclude_product_id) or p_id_str.startswith(str(exclude_product_id)):
                    continue

            if p.name.lower() == new_name:
                raise ValueError(f"Продукт с име '{name}' вече съществува в каталога.")
        return True
