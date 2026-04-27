import uuid
from datetime import datetime
from validators.movement_validator import MovementValidator
from models.movement_type import MovementType


class Movement:

    def __init__(self, movement_id, product_id, product_name, user_id,
                 location_id, movement_type, quantity, unit, description,
                 price=None, supplier_id=None, customer=None,
                 date=None, created=None, modified=None,
                 from_location_id=None, to_location_id=None):
        """Модел за движение. Тук държа само данните и логиката за ID и датите."""

        # Ако няма подадено ID – генерирам ново
        self.movement_id = str(movement_id) if movement_id else Movement.generate_id()
        # Основни данни
        self.product_id = str(product_id)
        self.product_name = product_name
        self.user_id = str(user_id)
        self.location_id = location_id
        self.movement_type = movement_type
        self.quantity = quantity
        self.unit = unit
        self.description = description
        self.price = price
        self.supplier_id = supplier_id
        self.customer = customer

        # Локации при MOVE
        self.from_location_id = from_location_id
        self.to_location_id = to_location_id

        # Дати
        now = Movement.now()
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        # Валидация
        MovementValidator.validate_all_fields(self)

    # Генерираме ново ID
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    # Текущ момент
    @staticmethod
    def now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_modified(self):
        """Обновявам датата при промяна."""
        self.modified = Movement.now()

    def to_dict(self):
        return {"movement_id": self.movement_id, "product_id": self.product_id, "product_name": self.product_name,
                "user_id": self.user_id, "location_id": self.location_id, "movement_type": self.movement_type.value
            if isinstance(self.movement_type, MovementType) else str(self.movement_type),
                "quantity": self.quantity, "unit": self.unit, "description": self.description, "price": self.price,
                "supplier_id": self.supplier_id, "customer": self.customer, "from_location_id": self.from_location_id,
                "to_location_id": self.to_location_id, "date": self.date, "created": self.created, "modified": self.modified}

    @staticmethod
    def from_dict(d):
        """Създавам Movement от JSON речник."""
        if not d:
            return None

        # Възстановяване на movement_type
        mt_raw = d.get("movement_type")
        mt = MovementType.IN  # по подразбиране

        if mt_raw:
            try:
                mt = MovementType(mt_raw)  # пробвам като стойност
            except Exception:
                try:
                    mt = MovementType[mt_raw]  # пробвам като име
                except Exception:
                    mt = MovementType.IN

        return Movement(movement_id=data.get("movement_id"), product_id=data.get("product_id"),
                        product_name=data.get("product_name") or data.get("product"), user_id=data.get("user_id"),
                        location_id=data.get("location_id"), movement_type=mt, quantity=data.get("quantity", 0),
                        unit=data.get("unit", "бр."), description=data.get("description", ""), price=data.get("price", 0.0),
                        supplier_id=data.get("supplier_id"), customer=data.get("customer"),
                        from_location_id=data.get("from_location_id"), to_location_id=data.get("to_location_id"),
                        date=data.get("date"), created=data.get("created"), modified=data.get("modified"))


    def __str__(self):
        m_type = self.movement_type.value if isinstance(self.movement_type, MovementType) else self.movement_type
        return (f"Движение {self.movement_id} | {m_type} | {self.quantity} {self.unit} | "
                f"Продукт: {self.product_name} | Склад ID: {self.location_id}")
