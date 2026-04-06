from enum import Enum
from datetime import datetime
from validators.movement_validator import MovementValidator

class MovementType(Enum):
    IN = "IN"
    OUT = "OUT"
    MOVE = "MOVE"


class Movement:
    def __init__(
            self, movement_id=None, product_id=None, user_id=None,
            location_id=None, movement_type=None, quantity=0,
            unit="бр.", description="", price=0.0, supplier_id=None, customer=None,
            from_location_id=None, to_location_id=None,
            date=None, created=None, modified=None):


        self.movement_id = str(movement_id) if movement_id is not None else None
        self.product_id = product_id
        self.user_id = user_id
        #  Локациите винаги са str (W1, W2, ...)
        self.location_id = str(location_id) if location_id is not None else None
        self.from_location_id = str(from_location_id) if from_location_id is not None else None
        self.to_location_id = str(to_location_id) if to_location_id is not None else None
        self.movement_type = movement_type
        self.quantity = quantity
        self.unit = unit
        self.description = description
        self.price = float(price)
        self.supplier_id = supplier_id
        self.customer = customer
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date = date or now
        self.created = created or now
        self.modified = modified or now
        # Централизирана валидация
        MovementValidator.validate_all(self)


    def to_dict(self):
        return {
            "movement_id": self.movement_id, "product_id": self.product_id,
            "user_id": self.user_id, "location_id": self.location_id,
            "movement_type": self.movement_type.name, "quantity": self.quantity,
            "unit": self.unit, "description": self.description,
            "price": self.price, "supplier_id": self.supplier_id,
            "customer": self.customer, "from_location_id": self.from_location_id,
            "to_location_id": self.to_location_id, "date": self.date,
            "created": self.created, "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        return Movement(
            movement_id=data.get("movement_id"),
            product_id=data.get("product_id"),
            user_id=data.get("user_id"),
            location_id=data.get("location_id"),
            movement_type=MovementType[data.get("movement_type")],
            quantity=data.get("quantity"),
            unit=data.get("unit"),
            description=data.get("description"),
            price=data.get("price", 0.0),
            supplier_id=data.get("supplier_id"),
            customer=data.get("customer"),
            from_location_id=data.get("from_location_id"),
            to_location_id=data.get("to_location_id"),
            date=data.get("date"),
            created=data.get("created"),
            modified=data.get("modified")
        )
