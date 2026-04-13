from datetime import datetime

class MovementValidator:

    ALLOWED_TYPES = ["IN", "OUT", "MOVE"]

    # INDEX VALIDATION (product, location, supplier)
    @staticmethod
    def validate_index(raw_index, max_len, label="избор"):
        try:
            index = int(raw_index)
        except ValueError:
            raise ValueError(f"Невалиден {label}. Трябва да е число.")

        if index < 0 or index >= max_len:
            raise ValueError(f"Невалиден {label}. Няма такъв елемент.")

        return index

    # MOVEMENT TYPE PARSING
    @staticmethod
    def parse_movement_type(raw):
        if raw not in ("0", "1", "2"):
            raise ValueError("Невалиден тип движение.")
        return ["IN", "OUT", "MOVE"][int(raw)]

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

        # MOVE → цена може да е 0.0
        if movement_type == "MOVE":
            if not price.strip():
                return 0.0
            try:
                return float(price)
            except ValueError:
                raise ValueError("Цената трябва да е число.")

        # IN / OUT → цена е задължителна и > 0
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

    @staticmethod
    def validate_move(product, from_loc, to_loc, quantity):
        MovementValidator.validate_locations(from_loc.location_id, to_loc.location_id, "MOVE")

        if product.quantity < quantity:
            raise ValueError("Недостатъчно количество за преместване.")

    # PRICE VALIDATION FOR IN/OUT
    @staticmethod
    def validate_price_for_type(price, movement_type):
        movement_type = str(movement_type).upper()
        if movement_type in ["IN", "OUT"] and price <= 0:
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

    # DATE VALIDATION
    @staticmethod
    def validate_date(date_str):
        if not date_str:
            return None

        # YYYY-MM-DD HH:MM:SS
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return date_str
        except:
            pass

        raise ValueError("Невалидна дата. Форматът трябва да е YYYY-MM-DD или YYYY-MM-DD HH:MM:SS.")

    # OPTIONAL INT PARSING
    @staticmethod
    def parse_optional_int(value, label):
        if not value.strip():
            return None
        if not value.isdigit():
            raise ValueError(f"{label} трябва да е число.")
        return int(value)

    # MAIN VALIDATION ENTRY
    @staticmethod
    def validate_all(movement):
        MovementValidator.validate_date(movement.date)
        MovementValidator.validate_movement_type(movement.movement_type)
        MovementValidator.validate_product_id(movement.product_id)
        MovementValidator.parse_quantity(str(movement.quantity))

        # Нормализиране на movement_type до IN / OUT / MOVE
        mt = movement.movement_type

        # Ако е enum → взимаме името, иначе директно текста
        if isinstance(mt, str):
            mtype = mt.strip().upper()
        else:
            mtype = mt.name.strip().upper()

        # MOVE → цена може да е 0
        if mtype == "MOVE":
            MovementValidator.validate_locations(
                movement.from_location_id,
                movement.to_location_id,
                mtype
            )
        else:
            # IN / OUT → цена трябва да е > 0
            MovementValidator.parse_price(str(movement.price), mtype)
            MovementValidator.validate_price_for_type(movement.price, mtype)

            if not movement.location_id:
                raise ValueError("Локацията е задължителна при IN/OUT.")
