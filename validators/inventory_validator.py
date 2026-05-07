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
        if not product_id:
            raise ValueError("ID на продукт е задължително.")
        if warehouse_id is not None and not warehouse_id:
            raise ValueError("ID на склад е задължително.")

    @staticmethod
    def _resolve_id(short_id, keys_list):
        """Намира пълното ID по въведено кратко ID.
        Ако потребителят въведе 'a1b2', търсим UUID, който започва с това."""
        short_id = str(short_id).lower()
        for full_id in keys_list:
            if full_id.lower().startswith(short_id):
                return full_id
        return None

    @staticmethod
    def validate_increase(product_id, product_name, warehouse_id, qty):
        InventoryValidator._validate_ids(product_id, warehouse_id)
        InventoryValidator.validate_string(product_name, "Име на продукт")
        val = InventoryValidator._validate_number(qty, "Количеството за IN")
        if val <= 0:
            raise ValueError("Количеството за IN трябва да бъде по-голямо от 0.")

    @staticmethod
    def validate_decrease(product_id, warehouse_id, qty, master_inventory):
        InventoryValidator._validate_ids(product_id, warehouse_id)
        val = InventoryValidator._validate_number(qty, "Количеството за OUT")
        if val <= 0:
            raise ValueError("Количеството за OUT трябва да бъде по-голямо от 0.")

        products = master_inventory.get("products", {})

        p_id_full = InventoryValidator._resolve_id(product_id, products.keys())
        if not p_id_full:
            raise ValueError(f"Продукт с ID {product_id} не съществува.")

        product_data = products[p_id_full]
        locations = product_data.get("locations", {})

        w_id_full = InventoryValidator._resolve_id(warehouse_id, locations.keys())
        if not w_id_full:
            raise ValueError(f"Локация {warehouse_id} не е намерена за този продукт.")

        current_qty = float(locations.get(w_id_full, 0.0))
        if current_qty < val:
            raise ValueError(f"Недостатъчна наличност! В склад {warehouse_id} има само {current_qty}.")

    @staticmethod
    def validate_move(product_id, from_wh, to_wh, qty, master_inventory):
        InventoryValidator._validate_ids(product_id)
        if str(from_wh) == str(to_wh):
            raise ValueError("Изходният и целевият склад не могат да бъдат еднакви.")

        val = InventoryValidator._validate_number(qty, "Количеството за MOVE")
        products = master_inventory.get("products", {})

        p_id_full = InventoryValidator._resolve_id(product_id, products.keys())
        if not p_id_full:
            raise ValueError("Продуктът не е намерен в инвентара.")

        locations = products[p_id_full].get("locations", {})
        from_wh_full = InventoryValidator._resolve_id(from_wh, locations.keys())

        if not from_wh_full:
            raise ValueError(f"Изходният склад {from_wh} не е намерен или е празен.")

        from_wh_qty = float(locations.get(from_wh_full, 0.0))
        if from_wh_qty < val:
            raise ValueError(f"Няма достатъчно стока за преместване. (Налично в {from_wh}: {from_wh_qty})")

    @staticmethod
    def validate_inventory_integrity(master_inventory):
        products = master_inventory.get("products", {})
        for p_id, data in products.items():
            wh_sum = sum(float(v) for v in data.get("locations", {}).values())
            total_recorded = float(data.get("total_stock", 0.0))
            if abs(wh_sum - total_recorded) > 0.0001:
                raise ValueError(f"Разсинхронизация при {data['name']}!")

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
