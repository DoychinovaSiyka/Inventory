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
        return datetime.now()

    @staticmethod
    def parse_date(value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return Movement.now()






    def __init__(self, movement_id=None, product_id=None, product_name="",
                 user_id=None, location_id=None, movement_type=None, quantity=None, unit="бр.", price=None,
                 supplier_id=None, customer=None, date=None, created=None, modified=None,
                 from_location_id=None, to_location_id=None):

        self.movement_id = str(movement_id) if movement_id else str(uuid.uuid4())
        self.product_id = str(product_id) if product_id else None
        self.user_id = str(user_id) if user_id else None
        self.product_name = product_name

        self.location_id = location_id
        self.from_location_id = from_location_id
        self.to_location_id = to_location_id

        self.movement_type = movement_type
        self.quantity = quantity
        self.price = price
        self.unit = unit

        self.supplier_id = supplier_id
        self.customer = customer

        #  Датите са datetime обекти
        self.date = Movement.parse_date(date)
        self.created = Movement.parse_date(created)
        self.modified = Movement.parse_date(modified)



    def update_modified(self):
        self.modified = Movement.now()




    def to_dict(self):
        """Превръща обекта в речник."""
        return {"movement_id": self.movement_id, "product_id": self.product_id,
                "product_name": self.product_name, "user_id": self.user_id,
                "location_id": self.location_id, "movement_type": self.movement_type.value, "quantity": self.quantity,
                "unit": self.unit, "price": self.price, "supplier_id": self.supplier_id, "customer": self.customer,
                "date": self.date, "created": self.created, "modified": self.modified, "from_location_id": self.from_location_id,
                "to_location_id": self.to_location_id}



    @staticmethod
    def from_dict(data):
        if not data or not isinstance(data, dict):
            return None

        mtype = data.get("movement_type")
        if mtype:
            try:
                mtype = MovementType[mtype]
            except KeyError:
                mtype = None

        return Movement(movement_id=data.get("movement_id"), product_id=data.get("product_id"),
                        product_name=data.get("product_name", ""), user_id=data.get("user_id"),
                        location_id=data.get("location_id"), movement_type=mtype, quantity=data.get("quantity"),
                        unit=data.get("unit", "бр."), price=data.get("price"), supplier_id=data.get("supplier_id"),
                        customer=data.get("customer"), date=data.get("date"), created=data.get("created"),
                        modified=data.get("modified"), from_location_id=data.get("from_location_id"),
                        to_location_id=data.get("to_location_id"))




    def __str__(self):
        mid = self.movement_id[:8] if self.movement_id else ""
        pid = self.product_id[:8] if self.product_id else ""
        mtype = self.movement_type.name if self.movement_type else "?"

        info = f"[Движение: {mid}] {mtype} | Продукт: {self.product_name} ({pid}) | Кол: {self.quantity} {self.unit}"

        if self.movement_type == MovementType.MOVE:
            if self.from_location_id and self.to_location_id:
                info += f" от {self.from_location_id[:8]} към {self.to_location_id[:8]}"
        else:
            if self.location_id:
                info += f" в склад {self.location_id[:8]}"

        return info
