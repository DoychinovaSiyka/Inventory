from enum import Enum


class MovementType(Enum):
    IN = "IN"
    OUT = "OUT"
    MOVE = "MOVE"


class Movement:
    def __init__(self, movement_id, product_id, user_id, location_id, movement_type,
                 quantity, unit, description, price, date,
                 created=None, modified=None,
                 supplier_id=None, customer=None,
                 from_location_id=None, to_location_id=None):

        self.movement_id = str(movement_id)
        self.product_id = product_id
        self.user_id = user_id
        # Основна локация (за IN/OUT)
        self.location_id = str(location_id) if location_id else None
        # Тип движение - Enum или String
        self.movement_type = movement_type
        self.quantity = quantity
        self.unit = unit
        self.description = description
        self.price = float(price)
        self.supplier_id = supplier_id
        self.customer = customer
        # MOVE специфични локации
        self.from_location_id = str(from_location_id) if from_location_id else None
        self.to_location_id = str(to_location_id) if to_location_id else None
        self.date = date
        self.created = created or date
        self.modified = modified or date

    def to_dict(self):
        """Превръща обекта в речник за JSON."""
        return {
            "movement_id": self.movement_id,
            "product_id": self.product_id,
            "user_id": self.user_id,
            "location_id": self.location_id,
            "movement_type": self.movement_type.name if isinstance(self.movement_type, MovementType) else str(self.movement_type),
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

    @staticmethod
    def from_dict(data):
        """Създава Movement от JSON речник."""
        if not data:
            return None
        # Опитвам да възстановим Enum
        mt_raw = data.get("movement_type")
        try:
            mt = MovementType(mt_raw)
        except ValueError:
            mt = mt_raw  # Ако не е валиден Enum, оставяме го като текст

        return Movement(
            movement_id=data.get("movement_id"),
            product_id=data.get("product_id"),
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
            date=data.get("date"),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        return f"Движение {self.movement_id} | Тип: {self.movement_type} | Количество: {self.quantity} {self.unit}"
