# validators/product_validator.py

from models.category import Category

class ProductValidator:

    @staticmethod
    def validate_name(name):
        if not name or not name.strip():
            raise ValueError("Името е задължително!")

    @staticmethod
    def validate_categories(categories):
        if not categories:
            raise ValueError("Трябва да изберете поне една категория.")

        for c in categories:
            if not isinstance(c, Category):
                raise ValueError("Невалидна категория.")

    @staticmethod
    def validate_quantity(quantity):
        if not isinstance(quantity, int):
            raise ValueError("Количеството трябва да е цяло число.")

        if quantity <= 0:
            raise ValueError("Количеството трябва да е положително число.")

    @staticmethod
    def validate_description(description):
        if not description or not description.strip():
            raise ValueError("Описанието е задължително!")

        if len(description) > 255:
            raise ValueError("Описанието не може да бъде повече от 255 символа.")

    @staticmethod
    def validate_price(price):
        if not isinstance(price, (int, float)):
            raise ValueError("Цената трябва да е число.")

        if price <= 0:
            raise ValueError("Цената трябва да е положителна.")

    @staticmethod
    def validate_all(name, categories, quantity, description, price):
        ProductValidator.validate_name(name)
        ProductValidator.validate_categories(categories)
        ProductValidator.validate_quantity(quantity)
        ProductValidator.validate_description(description)
        ProductValidator.validate_price(price)
