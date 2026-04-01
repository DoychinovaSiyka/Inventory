from enum import Enum
from datetime import datetime


class MovementType(Enum):
    IN = "IN"
    OUT = "OUT"
    MOVE = "MOVE"


def generate_next_id(existing_items):
    if not existing_items:
        return 1
    try:
        # movement_id остава число (ID на самия запис в базата)
        ids = [int(item["movement_id"]) for item in existing_items if "movement_id" in item]
        return max(ids) + 1
    except:
        return 1


class Movement:
    def __init__(
            self, movement_id=None, product_id=None, user_id=None,
            location_id=None, movement_type=None, quantity=0,
            unit="бр.", description="", price=0.0, supplier_id=None, customer=None,
            from_location_id=None, to_location_id=None,
            date=None, created=None, modified=None):

        # Техническото ID на записа остава int
        self.movement_id = int(movement_id) if movement_id is not None else None

        self.product_id = product_id
        self.user_id = user_id

        # ВАЖНО: Всички локации превръщаме в str, за да работят с "W1", "W2" и т.н.
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

        self.validate()

    def assign_new_id(self, existing_items):
        if self.movement_id is None:
            self.movement_id = generate_next_id(existing_items)

    def validate(self):
        if self.product_id is None:
            raise ValueError("product_id е задължително поле.")

        if self.user_id is None:
            raise ValueError("user_id е задължително поле.")

        if not isinstance(self.movement_type, MovementType):
            raise ValueError("movement_type трябва да е IN, OUT или MOVE.")

        if self.quantity <= 0:
            raise ValueError("quantity трябва да е > 0.")

        # Проверка за локации при MOVE
        if self.movement_type == MovementType.MOVE:
            if not self.from_location_id or not self.to_location_id:
                raise ValueError("MOVE движението изисква начална и крайна локация.")
            if self.from_location_id == self.to_location_id:
                raise ValueError("Началната и крайната локация не могат да бъдат еднакви.")

        # Валидация за цени
        if self.movement_type in [MovementType.IN, MovementType.OUT]:
            if self.price <= 0:
                raise ValueError(f"{self.movement_type.name} движение трябва да има цена > 0.")

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