import uuid


class InventoryValidator:

    @staticmethod
    def validate_string(text, field_name, min_len=2):
        if not text or not isinstance(text, str):
            raise ValueError(f"{field_name} трябва да бъде текстово поле.")
        clean_text = text.strip()
        if len(clean_text) < min_len:
            raise ValueError(f"{field_name} трябва да е поне {min_len} символа.")
        if clean_text.isdigit():
            raise ValueError(f"{field_name} не може да съдържа само цифри.")

        return clean_text

    @staticmethod
    def _validate_number(qty, field_name="Количество"):
        try:
            val = float(qty)
            if val < 0:
                raise ValueError(f"{field_name} не може да бъде отрицателно.")
            return val
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} трябва да бъде валидно число.")

    @staticmethod
    def _validate_ids(product_id, warehouse_id=None):
        # Проверка за задължителни ID-та
        if not product_id:
            raise ValueError("ID на продукт е задължително.")
        if warehouse_id is not None and not warehouse_id:
            raise ValueError("ID на склад е задължително.")

    @staticmethod
    def validate_increase(product_id, product_name, warehouse_id, qty):
        InventoryValidator._validate_ids(product_id, warehouse_id)
        InventoryValidator.validate_string(product_name, "Име на продукт")
        val = InventoryValidator._validate_number(qty, "Количеството за IN")
        if val <= 0:
            raise ValueError("Количеството за IN трябва да бъде по-голямо от 0.")

    @staticmethod
    def validate_decrease(product_id, warehouse_id, qty, master_inventory):
        # Проверка при OUT спрямо структурата на инвентара
        InventoryValidator._validate_ids(product_id, warehouse_id)
        val = InventoryValidator._validate_number(qty, "Количеството за OUT")
        if val <= 0:
            raise ValueError("Количеството за OUT трябва да бъде по-голямо от 0.")

        p_id_str = str(product_id)
        products = master_inventory.get("products", {})
        if p_id_str not in products:
            raise ValueError("Продуктът не съществува в системата за наличности.")

        product_data = products[p_id_str]
        locations = product_data.get("locations", {})
        current_qty = float(locations.get(str(warehouse_id), 0.0))
        if current_qty < val:
            raise ValueError(f"Недостатъчна наличност в склад {warehouse_id}! " 
                             f"Налично: {current_qty}, Заявка: {val}")

    @staticmethod
    def validate_move(product_id, product_name, from_wh, to_wh, qty, master_inventory):
        # Проверка при MOVE между два склада
        InventoryValidator._validate_ids(product_id)
        if str(from_wh) == str(to_wh):
            raise ValueError("Изходният и целевият склад не могат да бъдат еднакви.")

        val = InventoryValidator._validate_number(qty, "Количеството за MOVE")
        p_id_str = str(product_id)
        products = master_inventory.get("products", {})

        if p_id_str in products:
            from_wh_qty = float(products[p_id_str].get("locations", {}).get(str(from_wh), 0.0))
            if from_wh_qty < val:
                raise ValueError(f"Няма достатъчно стока в склад {from_wh} за преместване. "
                                 f"(Налично: {from_wh_qty})")
        else:
            raise ValueError("Продуктът не е намерен в инвентара.")

    @staticmethod
    def validate_inventory_integrity(master_inventory):
        # Проверка дали total_stock съвпада със сумата по локации
        products = master_inventory.get("products", {})
        for p_id, data in products.items():
            wh_sum = sum(float(v) for v in data.get("locations", {}).values())
            total_recorded = float(data.get("total_stock", 0.0))
            if abs(wh_sum - total_recorded) > 0.0001:
                raise ValueError(f"Разсинхронизация при {data['name']}! " 
                                 f"Сума по локации: {wh_sum}, "
                                 f"Общо записано: {total_recorded}.")

    @staticmethod
    def validate_movements(movements):
        if not isinstance(movements, list):
            raise ValueError("Списъкът с движения е в невалиден формат.")

        valid_types = {"IN", "OUT", "MOVE"}
        for idx, m in enumerate(movements):
            mtype = m.get("movement_type")
            if mtype not in valid_types:
                raise ValueError(f"Запис #{idx}: Невалиден тип '{mtype}'")

            qty = m.get("quantity")
            val = InventoryValidator._validate_number(qty, f"Количество в запис #{idx}")
            if val <= 0:
                raise ValueError(f"Запис #{idx}: Количеството трябва да е над 0.")
            if mtype == "MOVE":
                if not m.get("from_warehouse") or not m.get("to_warehouse"):
                    raise ValueError(f"Запис #{idx}: Липсва склад при MOVE.")
