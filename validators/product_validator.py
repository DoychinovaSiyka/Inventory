import uuid
from models.category import Category


class ProductValidator:
    @staticmethod
    def validate_uuid(value, field_name="ID"):
        """Проверява дали стойността е валиден UUID."""
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

    @staticmethod
    def validate_categories(categories):
        """Проверява списъка, като се оправя и с обекти, и със стрингове."""
        if not isinstance(categories, list):
            raise ValueError("Категориите трябва да са списък.")

        for c in categories:
            # Тук е логиката, която махнахме от модела
            if isinstance(c, Category):
                cid = str(c.category_id)
            else:
                cid = str(c)

            if not cid or cid.strip() == "":
                raise ValueError("Списъкът съдържа невалидна или празна категория.")

    @staticmethod
    def validate_quantity(quantity):
        try:
            q = float(quantity)
            if q < 0: raise ValueError()
        except:
            raise ValueError("Количеството трябва да е положително число.")

    @staticmethod
    def validate_unit(unit):
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")

    @staticmethod
    def validate_price(price):
        try:
            p = float(price)
            if p < 0: raise ValueError()
        except:
            raise ValueError("Цената трябва да е положително число.")

    @staticmethod
    def parse_int(value, field_name="стойност"):
        if value is None:
            raise ValueError(f"{field_name} е задължително поле.")

        value = value.strip()
        if not value.isdigit():
            raise ValueError(f"{field_name} трябва да е цяло число.")

        return int(value)

    @staticmethod
    def validate_all(product_id, name, categories, quantity, unit, description, price,
                     location_id, supplier_id, tags):
        """Вика всички проверки подред."""
        ProductValidator.validate_uuid(product_id, "Product ID")
        ProductValidator.validate_uuid(supplier_id, "Supplier ID")
        ProductValidator.validate_name(name)
        ProductValidator.validate_categories(categories)
        ProductValidator.validate_quantity(quantity)
        ProductValidator.validate_unit(unit)
        ProductValidator.validate_price(price)
        if not isinstance(location_id, str): raise ValueError("Локацията трябва да е текст.")
        if not isinstance(tags, list): raise ValueError("Tags трябва да са списък.")