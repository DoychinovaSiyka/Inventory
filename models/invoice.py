import uuid
from datetime import datetime

class Invoice:
    def __init__(
        self,
        invoice_id=None,
        movement_id=None,
        product="",
        quantity=0,
        unit_price=0.0,
        total_price=None,
        customer="",
        date=None,
        created=None,
        modified=None
    ):
        self.invoice_id = invoice_id or str(uuid.uuid4())
        self.movement_id = movement_id                     # връзка 1:1 с Movement
        self.product = product                             # име на продукта
        self.quantity = quantity                           # количество
        self.unit_price = unit_price                       # единична цена
        self.total_price = total_price or (quantity * unit_price)
        self.customer = customer                           # клиент
        self.date = date or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.created = created or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.modified = modified or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        return {
            "invoice_id": self.invoice_id,
            "movement_id": self.movement_id,
            "product": self.product,
            "quantity": self.quantity,
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
            unit_price=data.get("unit_price"),
            total_price=data.get("total_price"),
            customer=data.get("customer"),
            date=data.get("date"),
            created=data.get("created"),
            modified=data.get("modified")
        )
