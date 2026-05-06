import uuid
from datetime import datetime
from enum import Enum


class MovementType(Enum):
    IN = "IN"
    OUT = "OUT"
    MOVE = "MOVE"


class Movement:

    @staticmethod
    def now():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def __init__(self, movement_id, product_id, product_name, user_id, location_id, movement_type,
                 quantity, unit, price=None, supplier_id=None, customer=None, date=None,
                 created=None, modified=None, from_location_id=None, to_location_id=None):

        self.movement_id = movement_id or str(uuid.uuid4())
        self.product_id = product_id
        self.product_name = product_name
        self.user_id = user_id
        self.location_id = location_id
        self.movement_type = movement_type
        self.quantity = quantity
        self.unit = unit
        self.price = price
        self.supplier_id = supplier_id
        self.customer = customer

        now = Movement.now()
        self.date = date or now
        self.created = created or now
        self.modified = modified or now
        self.from_location_id = from_location_id
        self.to_location_id = to_location_id

    def update_modified(self):
        self.modified = Movement.now()

    def to_dict(self):
        return {"movement_id": self.movement_id, "product_id": self.product_id,
                 "product_name": self.product_name, "user_id": self.user_id, "location_id": self.location_id,
                "movement_type": self.movement_type.value, "quantity": self.quantity,
                "unit": self.unit, "price": self.price, "supplier_id": self.supplier_id,
                "customer": self.customer, "date": self.date, "created": self.created,
                "modified": self.modified, "from_location_id": self.from_location_id,
                "to_location_id": self.to_location_id}

    @staticmethod
    def from_dict(data):
        if not data:
            return None

        mtype = data.get("movement_type")
        if mtype not in ("IN", "OUT", "MOVE"):
            return None
        return Movement(movement_id=data.get("movement_id"), product_id=data.get("product_id"),
                        product_name=data.get("product_name"), user_id=data.get("user_id"),
                        location_id=data.get("location_id"), movement_type=MovementType[mtype],
                        quantity=data.get("quantity"), unit=data.get("unit"), price=data.get("price"),
                        supplier_id=data.get("supplier_id"), customer=data.get("customer"), date=data.get("date"),
                        created=data.get("created"), modified=data.get("modified"),
                        from_location_id=data.get("from_location_id"),
                        to_location_id=data.get("to_location_id"))
