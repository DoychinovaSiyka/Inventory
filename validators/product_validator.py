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
    def validate_description(description):
        """Проверява описанието на продукта."""
        if description is None:
            return

        if not isinstance(description, str):
            raise ValueError("Описанието трябва да бъде текстово поле.")

        desc = description.strip()
        if len(desc) < 3:
            raise ValueError("Описанието трябва да съдържа поне 3 символа.")

        if len(desc) > 1000:
            raise ValueError("Описанието не може да надвишава 1000 символа.")

    @staticmethod
    def validate_categories(categories):
        """Проверява списъка, като се оправя и с обекти, и със стрингове."""
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

    @staticmethod
    def validate_quantity(quantity):
        try:
            q = float(quantity)
            if q < 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Количеството трябва да е положително число.")

    @staticmethod
    def validate_unit(unit):
        """Мерната единица е задължителна."""
        if not unit or not isinstance(unit, str):
            raise ValueError("Мерната единица е задължителна.")

        if len(unit.strip()) < 1:
            raise ValueError("Мерната единица не може да бъде празна.")

    @staticmethod
    def validate_price(price):
        try:
            p = float(price)
            if p < 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValueError("Цената трябва да е положително число.")

    @staticmethod
    def _parse_float_internal(value, field_name="стойност"):
        """Вътрешен метод – парсва число, позволява запетая, връща float."""
        if isinstance(value, str):
            # Премахваме 'лв', 'лв.' и интервали
            value = value.replace("лв.", "").replace("лв", "").strip()
            # Позволяваме запетая
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

    @staticmethod
    def parse_optional_float(value: str, field_name="стойност"):
        if value is None:
            return None
        value = value.strip()
        if value == "":
            return None

        f = ProductValidator._parse_float_internal(value, field_name)
        if f < 0:
            raise ValueError(f"{field_name} не може да е отрицателна.")
        return f

    @staticmethod
    def parse_int(value, field_name="стойност"):
        if value is None:
            raise ValueError(f"{field_name} е задължително поле.")

        if isinstance(value, str):
            value = value.strip()
            if not value.isdigit():
                raise ValueError(f"{field_name} трябва да е цяло число.")

        try:
            return int(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} трябва да е цяло число.")

    @staticmethod
    def validate_all(product_id, name, categories, quantity, unit, description, price,
                     location_id, supplier_id, tags):
        """Вика всички проверки подред. UUID проверки"""
        if product_id:
            ProductValidator.validate_uuid(product_id, "Product ID")
        if supplier_id is not None:
            if isinstance(supplier_id, str) and supplier_id.strip() == "":
                raise ValueError("Supplier ID не може да бъде празен.")
            ProductValidator.validate_uuid(supplier_id, "Supplier ID")

        # Локациите НЕ са UUID - само проверяваме дали е текст
        if location_id and not isinstance(location_id, str):
            raise ValueError("Location ID трябва да е текст.")

        # Основни полета
        ProductValidator.validate_name(name)
        ProductValidator.validate_categories(categories)
        ProductValidator.validate_quantity(quantity)
        ProductValidator.validate_unit(unit)
        ProductValidator.validate_price(price)
        ProductValidator.validate_description(description)

        if tags is not None and not isinstance(tags, list):
            raise ValueError("Tags трябва да са списък.")
