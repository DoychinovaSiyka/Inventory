import uuid


class ProductValidator:
    @staticmethod
    def validate_name(name):
        if not name or not isinstance(name, str):
            raise ValueError("Името е задължително.")
        name = name.strip()
        if len(name) < 3:
            raise ValueError("Името трябва да е поне 3 символа.")
        return name

    @staticmethod
    def validate_description(description):
        if description is None or str(description).strip() == "":
            return ""
        desc = str(description).strip()
        if 0 < len(desc) < 3:
            raise ValueError("Описанието трябва да е поне 3 символа.")
        return desc

    @staticmethod
    def validate_unit(unit):
        u = str(unit).strip().lower()
        mapping = {"кг": "кг.", "kg": "кг.", "бр": "бр.", "pcs": "бр.", "л": "л.", "l": "л.", "пакет": "пакет"}
        # Търсим съвпадение в мапинга или връщаме оригиналното, ако е валидно
        return mapping.get(u, u if u else "бр.")

    @staticmethod
    def parse_float(value, field_name="стойност"):
        if value is None or str(value).strip() == "":
            raise ValueError(f"Полето '{field_name}' е задължително.")

        v = str(value).lower().replace("лв.", "").replace("лв", "").replace(",", ".").replace(" ", "").strip()
        try:
            num = float(v)
            if num <= 0:
                raise ValueError(f"{field_name} трябва да е над 0.")
            return round(num, 2)
        except:
            raise ValueError(f"Въведете валидно число за '{field_name}'.")

    @staticmethod
    def validate_unique_name(name, products, exclude_product_id=None):
        search_name = name.strip().lower()
        for p in products:
            if exclude_product_id and str(p.product_id) == str(exclude_product_id):
                continue
            if p.name.lower() == search_name:
                raise ValueError(f"Вече има продукт с име '{name}'.")
        return True