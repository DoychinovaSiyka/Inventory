import uuid


class ProductValidator:

    @staticmethod
    def validate_uuid(value, field_name="ID"):
        if value is None:
            return None

        val_str = str(value).strip()
        if len(val_str) == 8:
            if not val_str.isalnum():
                raise ValueError(f"{field_name} съдържа невалидни знаци.")
            return val_str

        if len(val_str) >= 32:
            try:
                if "-" in val_str:
                    uuid.UUID(val_str)
                return val_str
            except Exception:
                raise ValueError(f"Форматът на {field_name} не е валиден UUID.")
        raise ValueError(f"Въведете кратък код (8 знака) или пълен UUID за {field_name}.")


    @staticmethod
    def validate_name(name):
        if not name or not isinstance(name, str):
            raise ValueError("Името е задължително.")

        name = name.strip()
        if len(name) < 3:
            raise ValueError("Името трябва да е поне 3 символа.")
        if len(name) > 100:
            raise ValueError("Името е прекалено дълго.")
        return name

    @staticmethod
    def validate_description(description):
        if description is None or str(description).strip() == "":
            return ""

        desc = str(description).strip()
        if 0 < len(desc) < 3:
            raise ValueError("Описанието трябва да е поне 3 символа (или празно).")
        if len(desc) > 1000:
            raise ValueError("Описанието е твърде дълго.")
        return desc

    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str):
            raise ValueError("Трябва да изберете мерна единица.")

        u = unit.strip().lower()

        mapping = {"кг": "кг.", "kg": "кг.", "килограм": "кг.", "кило": "кг.",
                   "бр": "бр.", "брой": "бр.", "pcs": "бр.", "бройка": "бр.",
                   "л": "л.", "l": "л.", "литър": "л.", "пакет": "пакет", "пк": "пакет",
                   "pack": "пакет"}

        # Вземаме последната дума (ако потребителят е написал "2 пакета")
        parts = u.split()
        target = parts[-1]

        if target in mapping:
            return mapping[target]

        # Ограничен списък с позволени единици
        allowed = ["кг.", "бр.", "л.", "пакет"]
        if target not in allowed:
            if target.isalpha() and len(target) >= 1:
                return target
            raise ValueError(f"Невалидна единица. Позволени са: {', '.join(allowed)}")

        return target

    @staticmethod
    def parse_float(value, field_name="стойност"):
        if value is None or str(value).strip() == "":
            raise ValueError(f"Полето '{field_name}' е задължително.")

        # Почистваме входа от текст и символи за валута
        if isinstance(value, str):
            v = value.lower()
            v = v.replace("лв.", "").replace("лв", "")
            v = v.replace(",", ".")
            v = v.replace("bgn", "").replace(" ", "")
            value = v.strip()

        try:
            num = float(value)
            if num <= 0:
                raise ValueError(f"{field_name} трябва да е над 0.")
            return round(num, 2)
        except (ValueError, TypeError):
            raise ValueError(f"Въведете валидно число за '{field_name}'.")

    @staticmethod
    def validate_unique_name(name, products, exclude_product_id=None):
        if not name:
            return

        search_name = name.strip().lower()
        for p in products:
            if exclude_product_id:
                p_id = str(p.product_id)
                if p_id == str(exclude_product_id) or p_id.startswith(str(exclude_product_id)):
                    continue

            if p.name.lower() == search_name:
                raise ValueError(f"Вече има продукт с име '{name}'.")
        return True