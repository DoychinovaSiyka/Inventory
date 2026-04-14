from datetime import datetime


class MovementValidator:

    @staticmethod
    def validate_movement_type(movement_type):
        # Приема или int (0,1,2), или string ("IN","OUT","MOVE")
        if movement_type is None:
            raise ValueError("Типът движение е задължителен.")

        # Ако е enum → контролерът ще го подаде като string
        mt = str(movement_type).upper()

        if mt not in ("IN", "OUT", "MOVE"):
            raise ValueError("Невалиден тип движение.")


    @staticmethod
    def parse_movement_type(raw_type: str):
        raw_type = raw_type.strip()

        if raw_type == "0":
            return "IN"
        elif raw_type == "1":
            return "OUT"
        elif raw_type == "2":
            return "MOVE"

        raise ValueError("Невалиден тип движение. Използвайте 0=IN, 1=OUT, 2=MOVE.")

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
        try:
            p = float(price)
        except:
            raise ValueError("Невалидна цена.")
        if p < 0:
            raise ValueError("Цената не може да е отрицателна.")
        return round(p, 2)

    @staticmethod
    def normalize_movement_type(movement_type):
        # Връща string, за да няма нужда от импорт на MovementType
        mt = str(movement_type).upper()

        mapping = {
            "0": "IN",
            "1": "OUT",
            "2": "MOVE",
            "IN": "IN",
            "OUT": "OUT",
            "MOVE": "MOVE"
        }

        if mt not in mapping:
            raise ValueError("Невалиден тип движение.")

        return mapping[mt]

    @staticmethod
    def validate_user_exists(user_id, user_controller):
        user = user_controller.get_by_id(user_id)
        if not user:
            raise ValueError(f"Потребител с ID {user_id} не съществува.")

    @staticmethod
    def validate_product_exists(product_id, product_controller):
        product = product_controller.get_by_id(product_id)
        if not product:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

    @staticmethod
    def validate_in_out_rules(movement_type, product, quantity, supplier_id, customer):
        mt = str(movement_type).upper()

        if mt == "IN":
            if supplier_id is None:
                raise ValueError("При IN движение трябва да има доставчик.")

        if mt == "OUT":
            if product.quantity < quantity:
                raise ValueError("Недостатъчна наличност.")
            if not customer:
                raise ValueError("При OUT движение трябва да има клиент.")

        if mt == "MOVE":
            raise ValueError("MOVE може да се извършва само чрез move_product().")

    @staticmethod
    def validate_move_locations(from_location_id, to_location_id):
        if from_location_id == to_location_id:
            raise ValueError("MOVE трябва да е между различни локации.")

    @staticmethod
    def validate_move_stock(product_id, from_location_id, quantity, inventory_controller):
        record = inventory_controller._find(product_id, from_location_id)
        if not record or record["quantity"] < quantity:
            raise ValueError("Недостатъчна наличност в този склад.")

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
