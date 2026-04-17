from datetime import datetime


class MovementValidator:

    # BASIC TYPE VALIDATION
    @staticmethod
    def normalize_movement_type(movement_type):
        mt = str(movement_type).upper()
        mapping = {"0": "IN", "1": "OUT", "2": "MOVE", "IN": "IN", "OUT": "OUT", "MOVE": "MOVE"}
        if mt not in mapping:
            raise ValueError("Невалиден тип движение.")
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
        if not price:
            raise ValueError("Невалидна цена.")

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

    # EXISTENCE VALIDATION
    @staticmethod
    def validate_user_exists(user_id, user_controller):
        if not user_controller.get_by_id(user_id):
            raise ValueError(f"Потребител с ID {user_id} не съществува.")

    @staticmethod
    def validate_product_exists(product_id, product_controller):
        if not product_controller.get_by_id(product_id):
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

    @staticmethod
    def validate_location_exists(location_id, location_controller):
        if not location_controller.get_by_id(location_id):
            raise ValueError(f"Локация с ID {location_id} не съществува.")

    # BUSINESS RULES FOR IN / OUT
    @staticmethod
    def validate_in_out_rules(movement_type, product, quantity, supplier_id, customer,
                              inventory_controller, location_id):

        mt = str(movement_type).upper()

        if mt == "IN":
            if supplier_id is None:
                raise ValueError("При IN движение трябва да има доставчик.")

        if mt == "OUT":
            if inventory_controller is None:
                raise ValueError("Инвентарният контролер не е инициализиран.")

            available = inventory_controller.get_stock_for_location(product.product_id, location_id)

            if available < quantity:
                raise ValueError(f"Недостатъчна наличност! В този склад има само {available} {product.unit}.")

            if not customer:
                raise ValueError("При OUT движение трябва да има клиент.")

        if mt == "MOVE":
            raise ValueError("MOVE може да се извършва само чрез move_product().")

    @staticmethod
    def validate_location_rules(movement_type, product, target_location_id):
        mt = str(movement_type).upper()

        if mt == "OUT":
            if product.location_id and str(product.location_id) != str(target_location_id):
                raise ValueError("Продажбата трябва да е от склада, в който се намира продуктът.")

    # MOVE VALIDATION
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
        if inventory_controller is None:
            raise ValueError("Инвентарният контролер не е инициализиран.")

        # ✔ ОПРАВЕНО — използваме правилния метод
        available = inventory_controller.get_stock_for_location(product_id, from_location_id)

        if available < quantity:
            raise ValueError("Недостатъчна наличност в този склад за извършване на трансфер.")

    # DATE FILTERING
    @staticmethod
    def filter_by_date_range(movements, start_date, end_date):
        def parse(d):
            try:
                return datetime.strptime(d, "%Y-%m-%d")
            except:
                return None

        start = parse(start_date) if start_date else None
        end = parse(end_date) if end_date else None

        results = movements
        if start:
            results = [m for m in results if parse(m.date[:10]) and parse(m.date[:10]) >= start]
        if end:
            results = [m for m in results if parse(m.date[:10]) and parse(m.date[:10]) <= end]

        return results

    @staticmethod
    def validate_index(raw, length, label):
        if not raw.isdigit():
            raise ValueError(f"Невалиден избор за {label}.")
        index = int(raw)
        if index < 0 or index >= length:
            raise ValueError(f"Невалиден избор за {label}.")
        return index
