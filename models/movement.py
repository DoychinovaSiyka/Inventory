import uuid
from enum import Enum
from datetime import datetime


class MovementType(Enum):
    IN = "IN"
    OUT = "OUT"
    MOVE = "MOVE"


class MetaMovement(type):
    def __new__(cls, name, bases, namespace):

        if 'to_dict' not in namespace:
            def to_dict(self):
                return {
                    "movement_id": self.movement_id,
                    "product_id": self.product_id,
                    "user_id": self.user_id,
                    "location_id": self.location_id,
                    "movement_type": self.movement_type.name,
                    "quantity": self.quantity,
                    "unit": self.unit,
                    "price": self.price,
                    "description": self.description,
                    "supplier_id": self.supplier_id,   # ⭐ НОВО
                    "customer": self.customer,         # ⭐ НОВО
                    "date": self.date,
                    "created": self.created,
                    "modified": self.modified
                }
            namespace['to_dict'] = to_dict

        return super().__new__(cls, name, bases, namespace)


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
        supplier_id=None,     # ⭐ НОВО
        customer=None,        # ⭐ НОВО
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

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        self.validate()

    def __str__(self):
        base = (
            f"Движение ID: {self.movement_id}\n"
            f"Продукт ID: {self.product_id}\n"
            f"Потребител ID: {self.user_id}\n"
            f"Локация ID: {self.location_id}\n"
            f"Тип: {self.movement_type.name}\n"
            f"Количество: {self.quantity} {self.unit}\n"
            f"Цена: {self.price}\n"
            f"Описание: {self.description}\n"
        )

        #  Показваме доставчик или клиент
        if self.movement_type == MovementType.IN:
            base += f"Доставчик ID: {self.supplier_id}\n"
        elif self.movement_type == MovementType.OUT:
            base += f"Клиент: {self.customer}\n"

        base += f"Дата: {self.date}\n----------------------------------------"
        return base

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

        if self.price <= 0:
            raise ValueError("price трябва да е > 0.")

    @staticmethod
    def from_dict(data):
        return Movement(
            movement_id=data.get("movement_id"),
            product_id=data.get("product_id"),
            user_id=data.get("user_id"),
            location_id=data.get("location_id"),
            movement_type=MovementType(data.get("movement_type")),
            quantity=data.get("quantity"),
            unit=data.get("unit", "бр."),
            description=data.get("description"),
            price=data.get("price"),
            supplier_id=data.get("supplier_id"),   # ⭐ НОВО
            customer=data.get("customer"),         # ⭐ НОВО
            date=data.get("date"),
            created=data.get("created"),
            modified=data.get("modified")
        )
