import uuid


class MovementValidator:
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
    def validate_in_out_rules(movement_type, product, quantity, customer, inventory_controller, location_id):
        """Бизнес правила за наличност и клиенти."""
        mt = str(movement_type).upper()

        if mt == "OUT":
            if not customer or str(customer).strip() == "":
                raise ValueError("При продажба трябва да посочите клиент.")

            available = inventory_controller.get_stock(product.product_id, location_id)
            if available < quantity:
                raise ValueError(f"Недостатъчна наличност! Налично: {available} {product.unit}.")



    @staticmethod
    def validate_move_locations(from_loc, to_loc):
        if not from_loc or not to_loc:
            raise ValueError("Трансферът изисква два склада.")
        if str(from_loc) == str(to_loc):
            raise ValueError("Складовете трябва да са различни.")