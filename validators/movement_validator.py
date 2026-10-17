class MovementValidator:

    @staticmethod
    def normalize_movement_type(movement_type):
        if not movement_type:
            raise ValueError("Типът движение е задължителен.")

        t = str(movement_type).strip().upper()

        if t in ["IN", "OUT", "MOVE"]:
            return t

        if t.startswith("IN"):
            return "IN"
        if t.startswith("OUT"):
            return "OUT"
        if t.startswith(("MO", "TR")):
            return "MOVE"

        raise ValueError("Невалиден тип движение. Разрешени: IN, OUT, MOVE.")




    @staticmethod
    def parse_quantity(quantity):
        clean_qty = str(quantity).replace(",", ".").strip()

        try:
            q = float(clean_qty)
        except (ValueError, TypeError):
            raise ValueError("Невалидно количество. Въведете число.")

        if q <= 0:
            raise ValueError("Количеството трябва да е по-голямо от 0.")

        return round(q, 2)





    @staticmethod
    def parse_price(price, default_price=0.0) -> float:
        """Парсва цената от низ или я връща по подразбиране."""
        if price is None or str(price).strip() == "":
            return float(default_price)

        try:
            clean_price = str(price).lower().replace("лв", "").replace(",", ".").strip()
            prc = float(clean_price)
            if prc < 0:
                raise ValueError
            return round(prc, 2)
        except (ValueError, TypeError):
            raise ValueError("Невалидна цена.")




    @staticmethod
    def validate_in_rules(supplier_id):
        if not supplier_id or str(supplier_id).strip() == "":
            raise ValueError("При доставка (вход) трябва да посочите доставчик.")
        return True



    @staticmethod
    def validate_out_rules(product, quantity, customer, available_stock):
        if not customer or str(customer).strip() == "":
            raise ValueError("При продажба трябва да посочите клиент.")

        if available_stock < quantity:
            unit = "бр."
            if product is not None and hasattr(product, 'unit'):
                if isinstance(product.unit, str) and product.unit.strip():
                    unit = product.unit

            raise ValueError(f"Недостатъчна наличност! Налично: {available_stock} {unit}.")

        return True





    @staticmethod
    def validate_move_rules(product, quantity, available_stock, from_location_id, to_location_id):
        if not from_location_id or not to_location_id:
            raise ValueError("Трансферът изисква два склада.")

        if str(from_location_id) == str(to_location_id):
            raise ValueError("Изходният и целевият склад трябва да са различни.")

        if available_stock < quantity:
            unit = "бр."
            if product is not None and hasattr(product, 'unit'):
                if isinstance(product.unit, str) and product.unit.strip():
                    unit = product.unit

            raise ValueError(f"Недостатъчна наличност за преместване! Налично: {available_stock} {unit}.")

        return True