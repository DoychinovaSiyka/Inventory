from datetime import datetime
import uuid


class MovementValidator:

    # BASIC VALIDATION
    @staticmethod
    def validate_uuid(value, field_name):
        try:
            uuid.UUID(str(value))
        except:
            raise ValueError(f"{field_name} е невалидно UUID.")

    @staticmethod
    def normalize_movement_type(movement_type):
        mt = str(movement_type).upper()
        mapping = {"0": "IN", "1": "OUT", "2": "MOVE", "IN": "IN", "OUT": "OUT", "MOVE": "MOVE"}
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
        try:
            q = float(quantity)
        except:
            raise ValueError("Невалидно количество.")
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
        except:
            raise ValueError("Невалидна цена.")
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
        MovementValidator.validate_uuid(location_id, "Location ID")
        if not location_controller.get_by_id(location_id):
            raise ValueError(f"Локация с ID {location_id} не съществува.")

    @staticmethod
    def validate_supplier_exists(supplier_id, supplier_controller):
        if supplier_id is None:
            raise ValueError("При IN движение трябва да има доставчик.")
        MovementValidator.validate_uuid(supplier_id, "Supplier ID")
        if not supplier_controller.get_by_id(supplier_id):
            raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")


    # BUSINESS RULES FOR IN / OUT
    @staticmethod
    def validate_in_out_rules(movement_type, product, quantity, supplier_id, customer,
                              inventory_controller, location_id):

        mt = str(movement_type).upper()

        if mt == "IN":
            if supplier_id is None:
                raise ValueError("При IN движение трябва да има доставчик.")

        if mt == "OUT":
            if not customer:
                raise ValueError("При OUT движение трябва да има клиент.")

            available = inventory_controller.get_stock_for_location(product.product_id, location_id)
            if available < quantity:
                raise ValueError(f"Недостатъчна наличност! В този склад има само {available} {product.unit}.")


    @staticmethod
    def validate_move_locations(from_location_id, to_location_id):
        if str(from_location_id) == str(to_location_id):
            raise ValueError("MOVE трябва да е между различни локации.")

    @staticmethod
    def validate_move_allowed(product, from_location_id, to_location_id):
        current_loc = str(product.location_id)
        if str(to_location_id) == current_loc:
            raise ValueError("Не може да преместите продукта в същия склад, в който вече се намира.")
        if str(from_location_id) != current_loc:
            raise ValueError("Не може да преместите продукт от склад, в който той не се намира.")

    @staticmethod
    def validate_move_stock(product_id, from_location_id, quantity, inventory_controller):
        available = inventory_controller.get_stock_for_location(product_id, from_location_id)
        if available < quantity:
            raise ValueError("Недостатъчна наличност в този склад за извършване на трансфер.")


    @staticmethod
    def validate_date(date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except:
            raise ValueError("Невалидна дата. Форматът е YYYY-MM-DD.")
