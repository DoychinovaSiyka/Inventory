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

    def __init__(self, product, quantity, unit, unit_price, total_price, customer,
                 movement_id=None, date=None, created=None, modified=None, invoice_id=None):


        if invoice_id:
            self.invoice_id = str(invoice_id)
        else:
            self.invoice_id = Invoice.generate_id()

        if movement_id:
            self.movement_id = str(movement_id)
        else:
            self.movement_id = None


        self.product = product
        self.customer = customer
        self.quantity = float(quantity)
        self.unit = unit
        self.unit_price = float(unit_price)
        self.total_price = float(total_price)


        now_val = Invoice.now()
        if date:
            self.date = date
        else:
            self.date = now_val

        if created:
            self.created = created
        else:
            self.created = now_val

        if modified:
            self.modified = modified
        else:
            self.modified = now_val


        InvoiceValidator.validate_all(product=self.product, customer=self.customer,
                                      quantity=self.quantity, unit=self.unit,
                                      unit_price=self.unit_price, movement_id=self.movement_id,
                                      date=self.date, total_price=self.total_price)

    def update_modified(self):
        self.modified = Invoice.now()

    def to_dict(self):
        return {"invoice_id": self.invoice_id, "movement_id": self.movement_id,
                "product": self.product, "quantity": self.quantity, "unit": self.unit,
                "unit_price": self.unit_price, "total_price": self.total_price,
                "customer": self.customer, "date": self.date, "created": self.created,
                "modified": self.modified}

    @staticmethod
    def from_dict(data):
        if not data:
            return None

        return Invoice(invoice_id=data.get("invoice_id"), movement_id=data.get("movement_id"),
                       product=data.get("product", "Неизвестен"), quantity=data.get("quantity", 0),
                       unit=data.get("unit", "бр."), unit_price=data.get("unit_price", 0.0),
                       total_price=data.get("total_price", 0.0),
                       customer=data.get("customer", "Неизвестен"), date=data.get("date"),
                       created=data.get("created"), modified=data.get("modified"))

    def __str__(self):
        short_id = self.invoice_id[:8]
        return f"Фактура #{short_id} | Клиент: {self.customer} | Общо: {self.total_price:.2f} лв."
