class StockLogValidator:

    @staticmethod
    def validate_quantity(quantity):
        """Проверява дали е число и дали е положително. Връща float."""
        try:
            val = float(quantity)
            if val <= 0:
                raise ValueError("Количеството трябва да е положително число.")
            return val
        except (ValueError, TypeError):
            raise ValueError(f"Невалиден формат за количество: {quantity}")

    @staticmethod
    def validate_unit(unit):
        """Проверява за празна мерна единица и премахва интервалите."""
        if not unit or not str(unit).strip():
            raise ValueError("Мерната единица е задължителна.")
        return unit.strip()


    @staticmethod
    def validate_action(action):
        """Проверява дали действието е в позволения списък."""
        allowed_actions = ["add", "remove", "move", "move_in", "move_out", "in", "out"]
        clean_action = str(action).strip().lower()
        if clean_action not in allowed_actions:
            raise ValueError(f"Невалидно действие '{action}'. Позволени: {allowed_actions}")
        return clean_action