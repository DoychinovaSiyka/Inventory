from enum import Enum


class MovementType(Enum):
    IN = "IN"
    OUT = "OUT"
    MOVE = "MOVE"


class Movement:
    def __init__(self, movement_id, product_id, product_name, user_id,
                 location_id, movement_type, quantity, unit, description,
                 price, date, created=None, modified=None,
                 supplier_id=None, customer=None,
                 from_location_id=None, to_location_id=None,
                 location_name=None):

        # Унифициран ID
        self.id = str(movement_id)
        self.movement_id = self.id

        # Продукт
        self.product_id = str(product_id)
        # Тук е важна проверката: ако името е None или празно, слагаме "Неизвестен"
        self.product_name = product_name if product_name else "Неизвестен продукт"

        # Потребител
        self.user_id = str(user_id)

        # Локации
        self.location_id = str(location_id) if location_id else None
        self.location_name = location_name if location_name else "Неизвестен склад"

        self.from_location_id = str(from_location_id) if from_location_id else None
        self.to_location_id = str(to_location_id) if to_location_id else None

        # Тип движение
        self.movement_type = movement_type

        # Количество
        try:
            self.quantity = float(quantity)
        except (ValueError, TypeError):
            self.quantity = 0.0

        self.unit = unit or ""

        # Описание
        self.description = description or ""

        # Цена
        try:
            self.price = float(price) if price is not None else 0.0
        except (ValueError, TypeError):
            self.price = 0.0

        # Доставчик / Клиент
        self.supplier_id = supplier_id
        self.customer = customer

        # Дати
        self.date = date
        self.created = created or date
        self.modified = modified or date

    # ---------------------------------------------------------
    #  SAVE → JSON
    # ---------------------------------------------------------
    def to_dict(self):
        return {
            "movement_id": self.movement_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "user_id": self.user_id,
            "location_id": self.location_id,
            "location_name": self.location_name,
            "movement_type": self.movement_type.value if isinstance(self.movement_type, MovementType) else str(
                self.movement_type),
            "quantity": self.quantity,
            "unit": self.unit,
            "description": self.description,
            "price": self.price,
            "supplier_id": self.supplier_id,
            "customer": self.customer,
            "from_location_id": self.from_location_id,
            "to_location_id": self.to_location_id,
            "date": self.date,
            "created": self.created,
            "modified": self.modified
        }

    # ---------------------------------------------------------
    #  LOAD ← JSON
    # ---------------------------------------------------------
    @staticmethod
    def from_dict(data):
        if not data:
            return None

        # Обработка на типа движение ( Enum )
        mt_raw = data.get("movement_type")
        mt = MovementType.IN  # стойност по подразбиране

        if mt_raw:
            try:
                # Първо пробваме да го намерим по име на ключа (IN, OUT, MOVE)
                if mt_raw in MovementType.__members__:
                    mt = MovementType[mt_raw]
                # После пробваме по стойност ("IN", "OUT", "MOVE")
                else:
                    mt = MovementType(mt_raw)
            except (ValueError, KeyError):
                mt = MovementType.IN

        return Movement(
            movement_id=data.get("movement_id"),
            product_id=data.get("product_id"),
            # Опитваме се да вземем product_name, ако липсва - търсим под ключ 'product'
            product_name=data.get("product_name") or data.get("product"),
            user_id=data.get("user_id"),
            location_id=data.get("location_id"),
            movement_type=mt,
            quantity=data.get("quantity", 0),
            unit=data.get("unit", "бр."),
            description=data.get("description", ""),
            price=data.get("price", 0.0),
            supplier_id=data.get("supplier_id"),
            customer=data.get("customer"),
            from_location_id=data.get("from_location_id"),
            to_location_id=data.get("to_location_id"),
            location_name=data.get("location_name"),
            date=data.get("date"),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        m_type = self.movement_type.value if isinstance(self.movement_type, MovementType) else self.movement_type
        return f"Движение {self.movement_id} | {m_type} | {self.quantity} {self.unit} | Продукт: {self.product_name} | Склад: {self.location_name}"