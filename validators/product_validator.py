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
            return ""
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
            if isinstance(c, Category):
                cid = str(c.category_id)
            else:
                cid = str(c)
            if not cid or cid.strip() == "":
                raise ValueError("Списъкът съдържа невалидна или празна категория.")
        return categories

    @staticmethod
    def validate_quantity(quantity):
        try:
            q = float(quantity)
            if q < 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Количеството трябва да е положително число.")
        return round(q, 2)

    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")
        if len(unit.strip()) < 1:
            raise ValueError("Мерната единица не може да бъде празна.")
        return unit.strip()

    @staticmethod
    def validate_price(price):
        try:
            p = float(price)
            if p < 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Цената трябва да е положително число.")
        return round(p, 2)


    # PARSING HELPERS
    @staticmethod
    def _parse_float_internal(value, field_name="стойност"):
        if isinstance(value, str):
            value = value.replace("лв.", "").replace("лв", "").strip()
            value = value.replace(",", ".").strip()
        try:
            f = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} трябва да е число.")
        return round(f, 2)

    @staticmethod
    def parse_float(value, field_name="стойност"):
        f = ProductValidator._parse_float_internal(value, field_name)
        if f < 0:
            raise ValueError(f"{field_name} не може да е отрицателна.")
        return f


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

    @staticmethod
    def validate_stock_available(product, amount):
        if product.quantity < amount:
            raise ValueError("Недостатъчна наличност.")


    # MASTER VALIDATION
    @staticmethod
    def validate_all(product_id, name, categories, quantity, unit, description, price,
                     location_id, supplier_id, tags):
        ProductValidator.validate_uuid(product_id, "Product ID")
        ProductValidator.validate_uuid(supplier_id, "Supplier ID")
        ProductValidator.validate_name(name)
        ProductValidator.validate_categories(categories)
        ProductValidator.validate_quantity(quantity)
        ProductValidator.validate_unit(unit)
        ProductValidator.validate_price(price)
        ProductValidator.validate_description(description)
        if tags is not None and not isinstance(tags, list):
            raise ValueError("Tags трябва да са списък.")
