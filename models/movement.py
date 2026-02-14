import uuid
from enum import Enum
from datetime import datetime


# ENUM: MovementType
class MovementType(Enum):
    IN = "IN"
    OUT = "OUT"
    MOVE = "MOVE"


# META CLASS: MetaMovement
class MetaMovement(type):
    def __new__(cls, name, bases, namespace):

        # Автоматично добавяне на to_dict, ако липсва
        if "to_dict" not in namespace:
            def to_dict(self):
                return {
                    "movement_id": self.movement_id,
                    "product_id": self.product_id,
                    "user_id": self.user_id,
                    "location_id": self.location_id,
                    "movement_type": self.movement_type.name,
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
            namespace["to_dict"] = to_dict

        return super().__new__(cls, name, bases, namespace)


# CLASS: Movement
class Movement(metaclass=MetaMovement):
    def __init__(
        self,
        movement_id=None,
        product_id=None,
        user_id=None,
        location_id=None,
        movement_type=None,
        quantity=0,
        unit="бр.",
        description="",
        price=0.0,
        supplier_id=None,
        customer=None,
        from_location_id=None,
        to_location_id=None,
        date=None,
        created=None,
        modified=None
    ):
        self.movement_id = movement_id or str(uuid.uuid4())

        self.product_id = product_id
        self.user_id = user_id
        self.location_id = location_id
        self.movement_type = movement_type
        self.quantity = quantity
        self.unit = unit
        self.description = description
        self.price = price

        self.supplier_id = supplier_id
        self.customer = customer

        self.from_location_id = from_location_id
        self.to_location_id = to_location_id

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        self.validate()

    # VALIDATION
    def validate(self):
        if self.product_id is None:
            raise ValueError("product_id е задължително поле.")

        if self.user_id is None:
            raise ValueError("user_id е задължително поле.")

        if not isinstance(self.movement_type, MovementType):
            raise ValueError("movement_type трябва да е IN, OUT или MOVE.")

        if self.quantity <= 0:
            raise ValueError("quantity трябва да е > 0.")

        if not self.unit:
            raise ValueError("unit е задължително поле.")

        # IN LOGIC
        if self.movement_type == MovementType.IN:
            if self.price <= 0:
                raise ValueError("IN movement трябва да има цена > 0.")
            if self.supplier_id is None:
                raise ValueError("IN movement трябва да има supplier_id.")

        # OUT LOGIC
        elif self.movement_type == MovementType.OUT:
            if self.price <= 0:
                raise ValueError("OUT movement трябва да има цена > 0.")
            if self.customer is None:
                raise ValueError("OUT movement трябва да има customer.")

        # MOVE LOGIC
        elif self.movement_type == MovementType.MOVE:
            if self.from_location_id is None or self.to_location_id is None:
                raise ValueError("MOVE movement трябва да има from_location_id и to_location_id.")

            if self.from_location_id == self.to_location_id:
                raise ValueError("MOVE movement трябва да е между различни локации.")

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
            price=data.get("price"),
            supplier_id=data.get("supplier_id"),
            customer=data.get("customer"),
            from_location_id=data.get("from_location_id"),
            to_location_id=data.get("to_location_id"),
            date=data.get("date"),
            created=data.get("created"),
            modified=data.get("modified")
        )
