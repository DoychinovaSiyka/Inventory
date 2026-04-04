from datetime import datetime
from validators.invoice_validator import InvoiceValidator


def generate_next_invoice_id(existing_items):
    # ако няма фактури - започваме от 1
    if not existing_items:
        return 1

    try:
        ids = [int(item.get("invoice_id", 0)) for item in existing_items]
        return max(ids) + 1
    except:
        return 1


class Invoice:
    def __init__(self, invoice_id=None, movement_id=None, product="",
                 quantity=0, unit="", unit_price=0.0, total_price=None,
                 customer="", date=None, created=None, modified=None):

        # id на фактурата (auto increment)
        self.invoice_id = int(invoice_id) if invoice_id is not None else None

        # връзка към movement (1:1)
        self.movement_id = int(movement_id) if movement_id is not None else None

        self.product = product
        self.quantity = round(float(quantity), 2)
        self.unit = unit
        self.unit_price = round(float(unit_price), 2)

        if total_price is None:
            self.total_price = round(self.quantity * self.unit_price, 2)
        else:
            self.total_price = round(float(total_price), 2)

        self.customer = customer

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        # Валидацията вече е отделена
        InvoiceValidator.validate_all(
            self.product,
            self.customer,
            self.quantity,
            self.unit,
            self.unit_price,
            self.movement_id
        )

    def assign_new_id(self, existing_items):
        # извиква се от контролера, ако id липсва
        if self.invoice_id is None:
            self.invoice_id = generate_next_invoice_id(existing_items)

    def to_dict(self):
        # конвертиране към dict за json
        return {
            "invoice_id": self.invoice_id,
            "movement_id": self.movement_id,
            "product": self.product,
            "quantity": self.quantity,
            "unit": self.unit,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "customer": self.customer,
            "date": self.date,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        # създаване на invoice от json речник
        return Invoice(
            invoice_id=data.get("invoice_id"),
            movement_id=data.get("movement_id"),
            product=data.get("product"),
            quantity=data.get("quantity"),
            unit=data.get("unit", "бр."),
            unit_price=data.get("unit_price"),
            total_price=data.get("total_price"),
            customer=data.get("customer"),
            date=data.get("date"),
            created=data.get("created"),
            modified=data.get("modified")
        )
