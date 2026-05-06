from datetime import datetime
import uuid


class MovementValidator:

    @staticmethod
    def validate_uuid(value, field_name):
        if value is None or str(value).strip() == "":
            raise ValueError(f"{field_name} е задължително.")
        try:
            uuid.UUID(str(value))
        except Exception:
            raise ValueError(f"{field_name} е невалидно UUID.")

    @staticmethod
    def normalize_movement_type(movement_type):
        mt = str(movement_type).strip().upper()
        mapping = {"0": "IN", "1": "OUT", "2": "MOVE",
                   "IN": "IN", "OUT": "OUT", "MOVE": "MOVE"}
        if mt not in mapping:
            raise ValueError("Невалиден тип движение. Допустими: IN, OUT, MOVE.")
        return mapping[mt]

    @staticmethod
    def validate_movement_type(movement_type):
        if movement_type not in ("IN", "OUT", "MOVE"):
            raise ValueError("Невалиден тип движение.")

    @staticmethod
    def validate_description(description):
        if description is None:
            raise ValueError("Описанието е задължително.")
        if not isinstance(description, str):
            raise ValueError("Описанието трябва да е текст.")
        desc = description.strip()
        if len(desc) < 3:
            raise ValueError("Описанието трябва да е поне 3 символа.")
        if len(desc) > 500:
            raise ValueError("Описанието е твърде дълго.")

    @staticmethod
    def parse_quantity(quantity):
        if quantity is None or str(quantity).strip() == "":
            raise ValueError("Количество е задължително.")

        raw = str(quantity).lower().strip().replace(",", ".")

        for token in ["бр.", "бр", "кг.", "кг", "kg", "л.", "л", "l", " "]:
            raw = raw.replace(token, "")
        try:
            q = float(raw)
        except Exception:
            raise ValueError("Невалидно количество. Въведете число (пример: 5 или 12.5).")

        if q <= 0:
            raise ValueError("Количество трябва да е > 0.")

        return round(q, 2)

    @staticmethod
    def parse_price(price):
        if price is None or str(price).strip() == "":
            raise ValueError("Цената е задължителна.")
        p = str(price).lower().strip()
        for token in ["лв.", "лв", "lv.", "lv", " "]:
            p = p.replace(token, "")
        p = p.replace(",", ".")

        try:
            value = float(p)
        except Exception:
            raise ValueError("Невалидна цена. Въведете число.")
        if value < 0:
            raise ValueError("Цената не може да е отрицателна.")
        return round(value, 2)

    @staticmethod
    def validate_user_exists(user_id, user_controller):
        MovementValidator.validate_uuid(user_id, "User ID")
        if not user_controller.get_by_id(user_id):
            raise ValueError(f"Потребител с ID {user_id} не съществува.")

    @staticmethod
    def validate_product_exists(product_id, product_controller):
        MovementValidator.validate_uuid(product_id, "Product ID")
        if not product_controller.get_by_id(product_id):
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

    @staticmethod
    def validate_location_exists(location_id, location_controller):
        return MovementValidator.validate_location_id(location_id, location_controller)

    @staticmethod
    def validate_location_id(loc_id, location_controller):
        if loc_id is None or str(loc_id).strip() == "":
            raise ValueError("Location ID е задължително.")

        loc = str(loc_id).strip()
        if loc.isdigit():
            num = int(loc)
            locations = location_controller.get_all()
            if not locations:
                raise ValueError("Няма дефинирани локации.")
            if num < 1 or num > len(locations):
                raise ValueError(f"Невалиден номер на локация. Допустими: 1–{len(locations)}.")
            return locations[num - 1].location_id

        if loc.upper().startswith("W") and loc[1:].isdigit():
            code = loc.upper()
            if not location_controller.get_by_id(code):
                raise ValueError(f"Локация {code} не съществува.")
            return code

        raise ValueError("Невалиден Location ID. Допустими: 1–9 или W1–W9.")

    @staticmethod
    def validate_in_out_rules(movement_type, product, quantity,
                              customer, inventory_controller, location_id):

        mt = str(movement_type).upper()
        if mt == "IN":
            if customer:
                raise ValueError("При IN движение не може да има клиент.")

        if mt == "OUT":
            if not customer or str(customer).strip() == "":
                raise ValueError("При OUT движение трябва да има клиент.")

            if inventory_controller is None:
                raise ValueError("InventoryController липсва.")
            if product is None:
                raise ValueError("Липсва продукт за проверка на наличност.")
            if location_id is None:
                raise ValueError("Липсва локация за проверка на наличност.")

            available = inventory_controller.get_stock_for_location(product.product_id, location_id)
            if available < quantity:
                raise ValueError(f"Недостатъчна наличност! В този склад има само {available} "
                                 f"{product.unit}.")

        if mt == "MOVE":
            if customer:
                raise ValueError("MOVE не може да има клиент.")

    @staticmethod
    def validate_move_locations(from_location_id, to_location_id):
        if from_location_id is None or to_location_id is None:
            raise ValueError("MOVE изисква две локации.")
        if str(from_location_id) == str(to_location_id):
            raise ValueError("MOVE трябва да е между различни локации.")

    @staticmethod
    def validate_move_stock(product_id, from_location_id, quantity, inventory_controller):
        if inventory_controller is None:
            raise ValueError("InventoryController липсва.")
        if product_id is None:
            raise ValueError("Липсва продукт за MOVE.")
        available = inventory_controller.get_stock_for_location(product_id, from_location_id)
        if available < quantity:
            raise ValueError("Недостатъчна наличност за трансфер.")

    @staticmethod
    def validate_date(date_str):
        if date_str is None or str(date_str).strip() == "":
            raise ValueError("Датата е задължителна. Форматът е YYYY-MM-DD.")
        try:
            datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except Exception:
            raise ValueError("Невалидна дата. Форматът е YYYY-MM-DD.")
