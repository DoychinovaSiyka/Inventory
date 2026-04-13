class ProductValidator:

    @staticmethod
    def validate_name(name):
        if not name or not isinstance(name, str):
            raise ValueError("Името на продукта е задължително.")

    @staticmethod
    def validate_categories(categories):
        if not isinstance(categories, list):
            raise ValueError("Категориите трябва да са списък.")
        for c in categories:
            if not c or not isinstance(c, str):
                raise ValueError("Невалидна категория.")

    @staticmethod
    def validate_quantity(quantity):
        try:
            q = float(quantity)
        except:
            raise ValueError("Количество трябва да е число.")
        if q < 0:
            raise ValueError("Количество не може да е отрицателно.")

    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")

    @staticmethod
    def validate_description(description):
        if description is None:
            return
        if not isinstance(description, str):
            raise ValueError("Описанието трябва да е текст.")

    @staticmethod
    def validate_price(price):
        try:
            p = float(price)
        except:
            raise ValueError("Цената трябва да е число.")
        if p < 0:
            raise ValueError("Цената не може да е отрицателна.")

    @staticmethod
    def validate_location(location_id):
        if not location_id or not isinstance(location_id, str):
            raise ValueError("Локацията е задължителна.")

    @staticmethod
    def validate_supplier(supplier_id):
        if supplier_id is None:
            return
        if not isinstance(supplier_id, str):
            raise ValueError("supplier_id трябва да е UUID string.")

    @staticmethod
    def validate_tags(tags):
        if not isinstance(tags, list):
            raise ValueError("tags трябва да е списък.")
        for t in tags:
            if not isinstance(t, str):
                raise ValueError("Всеки tag трябва да е string.")

    @staticmethod
    def validate_all(name, categories, quantity, unit, description, price, location_id, supplier_id, tags):
        ProductValidator.validate_name(name)
        ProductValidator.validate_categories(categories)
        ProductValidator.validate_quantity(quantity)
        ProductValidator.validate_unit(unit)
        ProductValidator.validate_description(description)
        ProductValidator.validate_price(price)
        ProductValidator.validate_location(location_id)
        ProductValidator.validate_supplier(supplier_id)
        ProductValidator.validate_tags(tags)
