import uuid

class InventoryValidator:

    @staticmethod
    def _validate_number(qty, field_name="Количество"):
        """Помощен метод за проверка на число."""
        try:
            val = float(qty)
            if val < 0:
                raise ValueError(f"{field_name} не може да бъде отрицателно.")
            return val
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} трябва да бъде валидно число.")

    @staticmethod
    def validate_initial_stock(product_id, product_name, warehouse_id, qty):
        InventoryValidator._validate_number(qty, "Началното количество")
        if not product_id or not warehouse_id:
            raise ValueError("ID на продукт и склад са задължителни.")

    @staticmethod
    def validate_increase(product_id, product_name, warehouse_id, qty):
        val = InventoryValidator._validate_number(qty, "Количеството за IN")
        if val == 0:
            raise ValueError("Количеството за IN трябва да бъде по-голямо от 0.")

    @staticmethod
    def validate_decrease(product_id, warehouse_id, qty, stock):
        val = InventoryValidator._validate_number(qty, "Количеството за OUT")
        if val == 0:
            raise ValueError("Количеството за OUT трябва да бъде по-голямо от 0.")

        # Намиране на записа (кастваме към str за сигурност при търсенето)
        record = next((i for i in stock
                       if str(i["product_id"]) == str(product_id)
                       and str(i["warehouse"]) == str(warehouse_id)), None)

        if not record:
            raise ValueError(f"Продуктът не е намерен в склад {warehouse_id}.")
        if record["quantity"] < val:
            raise ValueError(f"Недостатъчна наличност! Налично: {record['quantity']}, Заявка: {val}")

    @staticmethod
    def validate_move(product_id, product_name, from_wh, to_wh, qty):
        if str(from_wh) == str(to_wh):
            raise ValueError("Изходният и целевият склад не могат да бъдат еднакви.")
        InventoryValidator._validate_number(qty, "Количеството за MOVE")

    @staticmethod
    def validate_movements(movements):
        """Проверка при rebuild на целия склад."""
        if not isinstance(movements, list):
            raise ValueError("Списъкът с движения е невалиден.")

        valid_types = {"IN", "OUT", "MOVE"}
        for m in movements:
            if m.get("movement_type") not in valid_types:
                raise ValueError(f"Невалиден тип движение в историята: {m.get('movement_type')}")
            if "product_id" not in m or "quantity" not in m:
                raise ValueError("Липсващи задължителни данни в историята на движенията.")