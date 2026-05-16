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
        desc = str(description).strip()
        if desc and len(desc) < 3:
            raise ValueError("Описанието трябва да е поне 3 символа.")
        return desc

    @staticmethod
    def validate_unique_name(name, products, exclude_product_id=None):
        search_name = name.strip().lower()
        for p in products:
            if exclude_product_id and str(p.product_id) == str(exclude_product_id):
                continue
            if p.name.lower() == search_name:
                raise ValueError(f"Вече има продукт с име '{name}'.")
        return True

    @staticmethod
    def parse_float(value, field_name="цена"):
        v = str(value).lower().replace("лв", "").replace(",", ".").replace(" ", "").strip()
        try:
            num = float(v)
            if num <= 0:
                raise ValueError(f"{field_name} трябва да е положително число.")
            return round(num, 2)
        except ValueError:
            raise ValueError(f"Въведете валидно число за '{field_name}'.")

    @staticmethod
    def validate_unit(unit):
        u = str(unit).strip()
        return u if u else "бр."