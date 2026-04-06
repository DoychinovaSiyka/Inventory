class StockLogValidator:

    @staticmethod
    def validate_quantity(quantity):
        if quantity <= 0:
            raise ValueError("Количеството трябва да е по-голямо от 0.")


    @staticmethod
    def validate_unit(unit):
        if not unit or not unit.strip():
            raise ValueError("Мерната единица е задължителна.")


    @staticmethod
    def validate_action(action):
        allowed_actions = ["add", "remove", "move", "move_in", "move_out"]
        if action not in allowed_actions:
            raise ValueError(f"Невалидно действие '{action}'. Позволени: {allowed_actions}")
