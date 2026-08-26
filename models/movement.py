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

    def __init__(self, movement_id=None, product_id=None, product_name="", user_id=None,
                 location_id=None, movement_type=MovementType.IN, quantity=0.0, unit="бр.",
                 price=None, supplier_id=None, customer=None, date=None, created=None,
                 modified=None, from_location_id=None, to_location_id=None):

        self.movement_id = str(movement_id) if movement_id else str(uuid.uuid4())
        self.product_id = str(product_id) if product_id else ""
        self.product_name = str(product_name)
        self.user_id = str(user_id) if user_id else ""


        self.location_id = str(location_id) if location_id is not None and str(location_id).strip() != "" else None


        if isinstance(movement_type, MovementType):
            self.movement_type = movement_type
        elif movement_type is not None:
            try:
                self.movement_type = MovementType[str(movement_type).upper()]
            except (KeyError, ValueError):
                try:
                    self.movement_type = MovementType(str(movement_type).upper())
                except (KeyError, ValueError):
                    self.movement_type = MovementType.IN
        else:
            self.movement_type = MovementType.IN

        if quantity is not None:
            try:
                clean_qty = str(quantity).replace(",", ".").strip()
                self.quantity = float(clean_qty)
            except (ValueError, TypeError):
                self.quantity = 0.0
        else:
            self.quantity = 0.0

        self.unit = str(unit)

        if price is not None and str(price).strip() != "":
            try:
                clean_price = str(price).lower().replace("лв", "").replace(",", ".").strip()
                self.price = float(clean_price)
            except (ValueError, TypeError):
                self.price = 0.0
        else:
            self.price = 0.0

        self.supplier_id = str(supplier_id) if supplier_id else None
        self.customer = customer

        now_val = Movement.now()
        self.date = date if date else now_val
        self.created = created if created else now_val
        self.modified = modified if modified else now_val


        self.from_location_id = str(from_location_id) if from_location_id is not None and str(from_location_id).strip() != "" else None
        self.to_location_id = str(to_location_id) if to_location_id is not None and str(to_location_id).strip() != "" else None




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


        return Movement(movement_id=data.get("movement_id"), product_id=data.get("product_id"),
                        product_name=data.get("product_name", ""), user_id=data.get("user_id"), location_id=data.get("location_id"),
                        movement_type=data.get("movement_type"), quantity=data.get("quantity"), unit=data.get("unit", "бр."),
                        price=data.get("price"), supplier_id=data.get("supplier_id"), customer=data.get("customer"),
                        date=data.get("date"), created=data.get("created"), modified=data.get("modified"),
                        from_location_id=data.get("from_location_id"), to_location_id=data.get("to_location_id"))







    def __str__(self):
        mid = self.movement_id[:8] if self.movement_id else ""
        pid = self.product_id[:8] if self.product_id else ""
        mtype = self.movement_type.name

        info = f"[Движение: {mid}] {mtype} | Продукт: {self.product_name} ({pid}) | Кол: {self.quantity} {self.unit}"

        if self.movement_type == MovementType.MOVE:
            if self.from_location_id and self.to_location_id:
                info += f" от {self.from_location_id[:8]} към {self.to_location_id[:8]}"
        else:
            if self.location_id:
                info += f" в склад {self.location_id[:8]}"

        return info