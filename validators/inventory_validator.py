class InventoryValidator:

    @staticmethod
    def validate_initial_stock(product_id, product_name, warehouse_id, qty):
        if qty < 0:
            raise ValueError("Началното количество не може да е отрицателно.")

    @staticmethod
    def validate_increase(product_id, product_name, warehouse_id, qty):
        if qty <= 0:
            raise ValueError("Количество за IN трябва да е > 0.")

    @staticmethod
    def validate_decrease(product_id, warehouse_id, qty, stock):
        if qty <= 0:
            raise ValueError("Количество за OUT трябва да е > 0.")

        record = next((i for i in stock if i["product_id"] == product_id and i["warehouse"] == warehouse_id), None)
        if not record:
            raise ValueError("Няма такава наличност в този склад.")

        if record["quantity"] < qty:
            raise ValueError("Недостатъчна наличност.")

    @staticmethod
    def validate_move(product_id, product_name, from_wh, to_wh, qty):
        if from_wh == to_wh:
            raise ValueError("MOVE изисква различни складове.")
        if qty <= 0:
            raise ValueError("Количество за MOVE трябва да е > 0.")

    @staticmethod
    def validate_movements(movements):
        for m in movements:
            if m["movement_type"] not in ("IN", "OUT", "MOVE"):
                raise ValueError("Невалиден тип движение.")
