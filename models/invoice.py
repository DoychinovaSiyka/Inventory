import uuid
from datetime import datetime
from validators.invoice_validator import InvoiceValidator


class Invoice:

    @staticmethod
    def generate_id():
        return str(uuid.uuid4())

    @staticmethod
    def now():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def __init__(self, product, quantity, unit, unit_price, total_price, customer, movement_id=None,
                 date=None, created=None, modified=None, invoice_id=None):


        self.invoice_id = invoice_id or Invoice.generate_id()
        self.movement_id = str(movement_id) if movement_id else None  # Свързано движение (OUT)
        self.product = product
        self.customer = customer
        self.quantity = quantity
        self.unit = unit
        self.unit_price = unit_price
        self.total_price = total_price

        now = Invoice.now()
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        InvoiceValidator.validate_all(product=self.product, customer=self.customer, quantity=self.quantity,
                                      unit=self.unit, unit_price=self.unit_price, movement_id=self.movement_id,
                                      date=self.date, total_price=self.total_price)

    def update_modified(self):
        """Обновява датата на последна промяна."""
        self.modified = Invoice.now()

    def to_dict(self):
        """Конвертиране към речник за JSON."""
        return {"invoice_id": self.invoice_id, "movement_id": self.movement_id, "product": self.product,
                "quantity": self.quantity, "unit": self.unit, "unit_price": self.unit_price,
                "total_price": self.total_price, "customer": self.customer, "date": self.date,
                "created": self.created, "modified": self.modified}

    @staticmethod
    def from_dict(data):
        """Създаване на Invoice от JSON речник."""
        if not data:
            return None

        return Invoice(invoice_id=data.get("invoice_id"), movement_id=data.get("movement_id"),
                       product=data.get("product", "Неизвестен"), quantity=data.get("quantity", 0),
                       unit=data.get("unit", "бр."), unit_price=data.get("unit_price", 0.0),
                       total_price=data.get("total_price", 0.0), customer=data.get("customer", "Неизвестен"),
                       date=data.get("date"), created=data.get("created"), modified=data.get("modified"))

    def __str__(self):
        return f"Фактура {self.invoice_id} | Клиент: {self.customer} | Общо: {self.total_price} лв."
