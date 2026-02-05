import uuid
from datetime import datetime

class Invoice:
    def __init__(
        self,
        invoice_id=None,
        movement_id=None,
        product="",
        quantity=0,
        unit="",              # ← НОВО: мерна единица
        unit_price=0.0,
        total_price=None,
        customer="",
        date=None,
        created=None,
        modified=None
    ):
        # ID — UUID според документацията
        self.invoice_id = invoice_id or str(uuid.uuid4())

        # Movement → Invoice (1:1)
        self.movement_id = str(movement_id) if movement_id is not None else None

        # Основни полета
        self.product = product
        self.quantity = quantity
        self.unit = unit              # ← НОВО
        self.unit_price = unit_price

        # total_price — коригирано, за да не презаписва 0.0
        self.total_price = (
            total_price if total_price is not None else quantity * unit_price
        )

        self.customer = customer

        # Дати — съобразено с документациите
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        # Валидация според SRS
        self.validate()

    # -------------------------
    # ВАЛИДАЦИЯ
    # -------------------------
    def validate(self):
        if not self.product:
            raise ValueError("Продуктът е задължителен (според SRS).")

        if not self.customer:
            raise ValueError("Клиентът е задължителен (според SRS).")

        if self.quantity <= 0:
            raise ValueError("Quantity трябва да е > 0 (според SRS).")

        if not self.unit or not self.unit.strip():
            raise ValueError("Мерната единица е задължителна (според SRS).")  # ← НОВО

        if self.unit_price <= 0:
            raise ValueError("Unit price трябва да е > 0 (според SRS).")

        if self.movement_id is None:
            raise ValueError("movement_id е задължителен (според SRS).")

    # -------------------------
    # JSON сериализация
    # -------------------------
    def to_dict(self):
        return {
            "invoice_id": self.invoice_id,
            "movement_id": self.movement_id,
            "product": self.product,
            "quantity": self.quantity,
            "unit": self.unit,              # ← НОВО
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "customer": self.customer,
            "date": self.date,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        return Invoice(
            invoice_id=data.get("invoice_id"),
            movement_id=data.get("movement_id"),
            product=data.get("product"),
            quantity=data.get("quantity"),
            unit=data.get("unit", "бр."),   # ← НОВО (fallback)
            unit_price=data.get("unit_price"),
            total_price=data.get("total_price"),
            customer=data.get("customer"),
            date=data.get("date"),
            created=data.get("created"),
            modified=data.get("modified")
        )
