from models.movement import MovementType

class MovementValidator:

    @staticmethod
    def parse_quantity(quantity):
        if not quantity.strip():
            raise ValueError("Количеството е задължително.")

        try:
            quantity = float(quantity)   # ← ВЕЧЕ Е FLOAT
        except ValueError:
            raise ValueError("Количеството трябва да е число.")

        if quantity <= 0:
            raise ValueError("Количеството трябва да е положително.")

        return quantity

    @staticmethod
    def parse_price(price):
        if not price.strip():
            raise ValueError("Цената е задължителна.")

        try:
            price = float(price)
        except ValueError:
            raise ValueError("Цената трябва да е число.")

        if price <= 0:
            raise ValueError("Цената трябва да е положителна.")

        return price

    @staticmethod
    def validate_description(description):
        if not description or not description.strip():
            raise ValueError("Описанието е задължително.")

        if len(description.strip()) > 200:
            raise ValueError("Описанието е твърде дълго (максимум 200 символа).")

    @staticmethod
    def validate_movement_type(movement_type):
        if not isinstance(movement_type, MovementType):
            raise ValueError("movement_type трябва да бъде MovementType Enum.")

    @staticmethod
    def validate_product_id(product_id):
        if not isinstance(product_id, str):
            raise ValueError("product_id трябва да бъде текст (UUID).")

        if not product_id.strip():
            raise ValueError("product_id не може да бъде празен.")

    @staticmethod
    def validate_unit(unit):
        if not unit or not unit.strip():
            raise ValueError("Мерната единица е задължителна.")  # ← НОВО

        allowed_units = ["бр.", "кг", "г", "л", "мл", "стек", "кашон"]

        if unit not in allowed_units:
            raise ValueError(f"Невалидна мерна единица. Разрешени: {', '.join(allowed_units)}")

        return unit
