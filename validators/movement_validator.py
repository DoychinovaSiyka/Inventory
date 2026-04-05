class MovementValidator:

    ALLOWED_TYPES = ["IN", "OUT", "MOVE"]

    # QUANTITY PARSING
    @staticmethod
    def parse_quantity(quantity):
        if not quantity.strip():
            raise ValueError("Количеството е задължително.")
        try:
            quantity = float(quantity)
        except ValueError:
            raise ValueError("Количеството трябва да е число.")
        if quantity <= 0:
            raise ValueError("Количеството трябва да е положително.")
        return quantity

    # PRICE PARSING
    @staticmethod
    def parse_price(price, movement_type=None):
        movement_type = str(movement_type).upper()

        if movement_type == "MOVE":
            if not price.strip():
                return 0.0
            try:
                return float(price)
            except ValueError:
                raise ValueError("Цената трябва да е число.")

        if not price.strip():
            raise ValueError("Цената е задължителна.")
        try:
            price = float(price)
        except ValueError:
            raise ValueError("Цената трябва да е число.")
        if price <= 0:
            raise ValueError("Цената трябва да е положителна.")

        return price

    # DESCRIPTION VALIDATION
    @staticmethod
    def validate_description(description, movement_type=None):
        movement_type = str(movement_type).upper()

        if movement_type == "MOVE":
            return
        if not description or not description.strip():
            raise ValueError("Описанието е задължително.")
        if len(description.strip()) > 200:
            raise ValueError("Описанието е твърде дълго (максимум 200 символа).")

    # MOVEMENT TYPE VALIDATION
    @staticmethod
    def validate_movement_type(movement_type):
        # Ако е Enum → взимаме името му (IN, OUT, MOVE)
        if hasattr(movement_type, "name"):
            movement_type = movement_type.name

        movement_type = str(movement_type).upper()

        if movement_type not in MovementValidator.ALLOWED_TYPES:
            raise ValueError("movement_type трябва да бъде IN, OUT или MOVE.")

    # PRODUCT ID VALIDATION
    @staticmethod
    def validate_product_id(product_id):
        if not isinstance(product_id, str):
            raise ValueError("product_id трябва да бъде текст (UUID).")
        if not product_id.strip():
            raise ValueError("product_id не може да бъде празен.")

    # USER ID VALIDATION
    @staticmethod
    def validate_user_id(user_id):
        if user_id is None:
            raise ValueError("user_id е задължително поле.")

    # LOCATION VALIDATION
    @staticmethod
    def validate_locations(from_id, to_id, movement_type):
        movement_type = str(movement_type).upper()

        if movement_type == "MOVE":
            if not from_id or not to_id:
                raise ValueError("MOVE движението изисква начална и крайна локация.")
            if from_id == to_id:
                raise ValueError("Началната и крайната локация не могат да бъдат еднакви.")

        if from_id and not isinstance(from_id, str):
            raise ValueError("Началната локация трябва да е текст (код).")

        if to_id and not isinstance(to_id, str):
            raise ValueError("Крайната локация трябва да е текст (код).")

    # PRICE VALIDATION FOR IN/OUT
    @staticmethod
    def validate_price_for_type(price, movement_type):
        movement_type = str(movement_type).upper()

        if movement_type in ["IN", "OUT"]:
            if price <= 0:
                raise ValueError(f"{movement_type} движение трябва да има цена > 0.")

    # UNIT VALIDATION
    @staticmethod
    def validate_unit(unit):
        if not unit or not unit.strip():
            raise ValueError("Мерната единица е задължителна.")

        allowed_units = ["бр.", "кг", "г", "л", "мл", "стек", "кашон"]
        if unit not in allowed_units:
            raise ValueError(f"Невалидна мерна единица. Разрешени: {', '.join(allowed_units)}")
        return unit

    # MAIN VALIDATION ENTRY POINT
    @staticmethod
    def validate_all(movement):
        MovementValidator.validate_product_id(movement.product_id)
        MovementValidator.validate_user_id(movement.user_id)
        MovementValidator.validate_movement_type(movement.movement_type)
        MovementValidator.validate_unit(movement.unit)
        MovementValidator.validate_locations(
            movement.from_location_id,
            movement.to_location_id,
            movement.movement_type
        )
        MovementValidator.validate_price_for_type(movement.price, movement.movement_type)

        if movement.quantity <= 0:
            raise ValueError("quantity трябва да е > 0.")
