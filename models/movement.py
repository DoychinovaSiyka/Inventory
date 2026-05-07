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


        if not movement_id:
            self.movement_id = str(uuid.uuid4())
        else:
            self.movement_id = str(movement_id)

        self.product_id = str(product_id)
        self.product_name = product_name
        self.user_id = str(user_id)
        self.location_id = str(location_id) if location_id else None

        self.movement_type = movement_type
        self.quantity = float(quantity) if quantity is not None else 0.0
        self.unit = unit
        self.price = float(price) if price is not None else 0.0
        self.supplier_id = str(supplier_id) if supplier_id else None
        self.customer = customer

        now_val = Movement.now()
        self.date = date or now_val
        self.created = created or now_val
        self.modified = modified or now_val
        self.from_location_id = str(from_location_id) if from_location_id else None
        self.to_location_id = str(to_location_id) if to_location_id else None

    def update_modified(self):
        """Обновява времето на последна промяна."""
        self.modified = Movement.now()

    def to_dict(self):
        """Превръща обекта в речник."""
        return {"movement_id": self.movement_id, "product_id": self.product_id,
                "product_name": self.product_name, "user_id": self.user_id, "location_id": self.location_id,
                 "movement_type": self.movement_type.value, "quantity": self.quantity, "unit": self.unit,
                 "price": self.price, "supplier_id": self.supplier_id, "customer": self.customer,
                 "date": self.date, "created": self.created, "modified": self.modified,
                 "from_location_id": self.from_location_id, "to_location_id": self.to_location_id}

    @staticmethod
    def from_dict(data):
        if not data:
            return None

        mtype_str = data.get("movement_type")
        if mtype_str not in ("IN", "OUT", "MOVE"):
            return None

        return Movement(movement_id=data.get("movement_id"), product_id=data.get("product_id"),
                        product_name=data.get("product_name"), user_id=data.get("user_id"),
                        location_id=data.get("location_id"), movement_type=MovementType[mtype_str],
                        quantity=data.get("quantity"), unit=data.get("unit"), price=data.get("price"),
                        supplier_id=data.get("supplier_id"), customer=data.get("customer"), date=data.get("date"),
                        created=data.get("created"), modified=data.get("modified"),
                        from_location_id=data.get("from_location_id"), to_location_id=data.get("to_location_id"))

    def __str__(self):
        mid = self.movement_id[:8]
        pid = self.product_id[:8]
        mtype = self.movement_type.name

        info = f"[Движение: {mid}] {mtype} | Продукт: {self.product_name} ({pid}) | Кол: {self.quantity} {self.unit}"
        if mtype == "MOVE":
            info += f" от {self.from_location_id[:8]} към {self.to_location_id[:8]}"
        elif self.location_id:
            info += f" в склад {self.location_id[:8]}"

        return info