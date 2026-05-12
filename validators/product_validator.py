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
    def validate_unit(unit, allowed_units=None):
        """ Ако е подаден списък с разрешени единици, проверява срещу него."""
        u = str(unit).strip()
        if not u:
            return "бр."

        if allowed_units and u not in allowed_units:
            clean_u = u.lower().replace(".", "")
            for allowed in allowed_units:
                if clean_u in allowed.lower():
                    return allowed
            raise ValueError(f"Невалидна мерна единица: {u}")

        return u

    @staticmethod
    def parse_float(value, field_name="стойност"):
        """Парсва стринг към float с почистване на символи (лв, запетаи)."""
        if value is None or str(value).strip() == "":
            raise ValueError(f"Полето '{field_name}' е задължително.")


        v = str(value).lower().replace("лв", "").replace(",", ".").replace(" ", "").strip()
        try:
            num = float(v)
            if num <= 0:
                raise ValueError(f"{field_name} трябва да е положително число.")
            return round(num, 2)
        except ValueError:
            raise ValueError(f"Въведете валидно число за '{field_name}' (напр. 12.50).")


    @staticmethod
    def validate_unique_name(name, products, exclude_product_id=None):
        search_name = name.strip().lower()
        for p in products:
            if exclude_product_id and str(p.product_id) == str(exclude_product_id):
                continue
            if p.name.lower() == search_name:
                raise ValueError(f"Вече има продукт с име '{name}'.")
        return True