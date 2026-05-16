class InventoryValidator:
    @staticmethod
    def validate_string(text, field_name, min_len=2):
        if not text or not isinstance(text, str):
            raise ValueError(f"{field_name} трябва да бъде текстово поле.")
        clean_text = text.strip()
        if len(clean_text) < min_len:
            raise ValueError(f"{field_name} трябва да е поне {min_len} символа.")
        return clean_text

    @staticmethod
    def parse_and_validate_number(value, field_name="Количество"):
        if value is None or str(value).strip() == "":
            raise ValueError(f"Полето '{field_name}' е задължително.")

        if isinstance(value, (int, float)):
            val = float(value)
        else:
            # Изчистване на текстови добавки като 'кг', 'лв' и оправяне на запетаи
            cleaned = "".join(ch for ch in str(value) if ch.isdigit() or ch == "." or ch == ",")
            cleaned = cleaned.replace(",", ".")
            try:
                val = float(cleaned)
            except ValueError:
                raise ValueError(f"'{value}' не е валидно число за {field_name}.")

        if val < 0:
            raise ValueError(f"{field_name} не може да бъде отрицателно число.")
        return round(val, 3)

    @staticmethod
    def validate_stock_availability(requested_qty, available_qty, product_name="Продуктът"):
        if requested_qty > available_qty:
            raise ValueError(
                f"Недостатъчна наличност! Продукт: {product_name}. "
                f"Налично: {available_qty}, Заявено: {requested_qty}.")

    @staticmethod
    def validate_move_locations(from_wh_id, to_wh_id):
        if not from_wh_id or not to_wh_id:
            raise ValueError("Трансферът изисква начална и крайна локация.")
        if str(from_wh_id) == str(to_wh_id):
            raise ValueError("Началната и крайната локация не могат да бъдат еднакви.")