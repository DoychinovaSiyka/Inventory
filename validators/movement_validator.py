import uuid
from datetime import datetime


class MovementValidator:

    @staticmethod
    def validate_uuid(value, field_name):
        if value is None or str(value).strip() == "":
            raise ValueError(f"{field_name} е задължително поле.")

        val_str = str(value).strip()

        # Кратък код (8 символа)
        if len(val_str) == 8:
            if not all(c.isalnum() for c in val_str):
                raise ValueError(f"{field_name} съдържа невалидни символи.")
            return

        # Пълен UUID
        try:
            uuid.UUID(val_str)
        except Exception:
            raise ValueError(f"{field_name} е невалидно ID. Въведете 8 символа или пълен UUID.")

    @staticmethod
    def normalize_movement_type(movement_type):
        mt = str(movement_type).strip().upper()
        mapping = {
            "1": "IN", "2": "OUT", "3": "MOVE",
            "IN": "IN", "OUT": "OUT", "MOVE": "MOVE"
        }
        if mt not in mapping:
            raise ValueError("Невалиден тип движение. Допустими: IN, OUT, MOVE.")
        return mapping[mt]

    @staticmethod
    def parse_quantity(quantity):
        if quantity is None or str(quantity).strip() == "":
            raise ValueError("Количеството е задължително.")

        raw = str(quantity).lower().strip().replace(",", ".")

        # Премахване на мерни единици, ако са въведени
        for token in ["бр.", "бр", "кг.", "кг", "kg", "л.", "л", "l", " "]:
            raw = raw.replace(token, "")

        try:
            q = float(raw)
            if q <= 0:
                raise ValueError("Количеството трябва да е по-голямо от 0.")
            return round(q, 2)
        except:
            raise ValueError("Невалидно количество. Въведете число (напр. 5 или 12.50).")

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
            if value < 0:
                raise ValueError("Цената не може да е отрицателна.")
            return round(value, 2)
        except:
            raise ValueError("Невалидна цена. Въведете число.")

    @staticmethod
    def validate_user_exists(user_id, user_controller):
        user = user_controller.get_by_id(user_id)
        if not user:
            raise ValueError(f"Потребител с ID {user_id} не съществува.")
        return user.user_id

    @staticmethod
    def validate_product_exists(product_id, product_controller):
        product = product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")
        return product

    @staticmethod
    def validate_location_id(loc_id, location_controller):
        """Позволява избор на склад чрез:
        - номер от списъка (1, 2, 3…)
        - кратко ID (8 символа)
        - пълно ID"""
        if loc_id is None or str(loc_id).strip() == "":
            raise ValueError("Код на склад е задължителен.")

        loc_input = str(loc_id).strip()
        locations = location_controller.get_all()

        # Избор по номер
        if loc_input.isdigit() and len(loc_input) < 3:
            num = int(loc_input)
            if 1 <= num <= len(locations):
                return locations[num - 1].location_id
            raise ValueError(f"Невалиден номер. Изберете от 1 до {len(locations)}.")

        # Търсене по ID
        found_loc = location_controller.get_by_id(loc_input)
        if found_loc:
            return found_loc.location_id

        raise ValueError(f"Склад с ID/номер '{loc_input}' не е намерен.")

    @staticmethod
    def validate_in_out_rules(movement_type, product, quantity, customer, inventory_controller, location_id):
        mt = str(movement_type).upper()

        if mt == "IN" and customer:
            raise ValueError("При заприхождаване (IN) не може да има клиент.")

        if mt == "OUT":
            if not customer or str(customer).strip() == "":
                raise ValueError("При продажба (OUT) трябва да посочите име на клиент.")

            available = inventory_controller.get_total_stock_for_location(product.product_id, location_id)
            if available < quantity:
                raise ValueError(f"Недостатъчна наличност. В този склад има само {available} {product.unit}.")

        if mt == "MOVE" and customer:
            raise ValueError("Вътрешните премествания (MOVE) не използват клиент.")

    @staticmethod
    def validate_move_locations(from_loc, to_loc):
        if not from_loc or not to_loc:
            raise ValueError("MOVE операцията изисква изходен и целеви склад.")
        if str(from_loc) == str(to_loc):
            raise ValueError("Не можете да местите стока в същия склад.")

    @staticmethod
    def validate_date(date_str):
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        try:
            datetime.strptime(date_str.strip(), "%Y-%m-%d")
            return date_str.strip()
        except:
            raise ValueError("Невалидна дата. Използвайте формат ГГГГ-ММ-ДД.")
