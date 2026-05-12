class MovementValidator:

    @staticmethod
    def normalize_movement_type(movement_type):
        """Нормализира типа движение до IN, OUT или MOVE."""
        if not movement_type:
            raise ValueError("Типът движение е задължителен.")

        t = str(movement_type).strip().upper()

        if t in ["IN", "OUT", "MOVE"]:
            return t

        if t.startswith("IN"):
            return "IN"
        if t.startswith("OUT"):
            return "OUT"
        if t.startswith("MO") or t.startswith("TR"):
            return "MOVE"

        raise ValueError("Невалиден тип движение. Разрешени: IN, OUT, MOVE.")

    @staticmethod
    def parse_quantity(quantity):
        """Превръща входа в число и чисти мерни единици."""
        if quantity is None or str(quantity).strip() == "":
            raise ValueError("Количеството е задължително.")

        raw = str(quantity).lower().strip().replace(",", ".")
        tokens = ["бр.", "бр", "кг.", "кг", "kg", "л.", "л", "l", " "]
        for t in tokens:
            raw = raw.replace(t, "")

        try:
            q = float(raw)
            if q <= 0:
                raise ValueError("Количеството трябва да е по-голямо от 0.")
            return round(q, 2)
        except Exception:
            raise ValueError("Невалидно количество. Въведете число.")

    @staticmethod
    def validate_in_rules(product, quantity):
        if quantity <= 0:
            raise ValueError("Количеството трябва да е положително.")
        return True

    @staticmethod
    def validate_out_rules(product, quantity, customer, inventory_controller, location_id):
        if not customer or str(customer).strip() == "":
            raise ValueError("При продажба трябва да посочите клиент.")

        available = inventory_controller.get_stock(product.product_id, location_id)
        if available < quantity:
            raise ValueError(f"Недостатъчна наличност! Налично: {available} {product.unit}.")
        return True

    @staticmethod
    def validate_move_rules(product, quantity, inventory_controller, from_location_id, to_location_id):
        if not from_location_id or not to_location_id:
            raise ValueError("Трансферът изисква два склада.")

        if str(from_location_id) == str(to_location_id):
            raise ValueError("Складовете трябва да са различни.")

        available = inventory_controller.get_stock(product.product_id, from_location_id)
        if available < quantity:
            raise ValueError(f"Недостатъчна наличност за преместване! Налично: {available} {product.unit}.")
        return True
