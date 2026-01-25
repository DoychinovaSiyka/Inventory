class MovementValidator:

    @staticmethod
    def parse_quantity(quantity):
        if not quantity.strip():
            raise ValueError("Количеството е задължително.")

        try:
            quantity = int(quantity)
        except ValueError:
            raise ValueError("Количеството трябва да е цяло число.")

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

    @staticmethod
    def validate_movement_type(movement_type_num):
        if movement_type_num not in [0, 1]:
            raise ValueError("Невалиден тип движение. Изберете 0 или 1.")


