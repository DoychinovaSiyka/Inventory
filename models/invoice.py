import uuid
from datetime import datetime
from validators.invoice_validator import InvoiceValidator


class Invoice:
    def __init__(self, invoice_id=None, movement_id=None, product="",
                 quantity=0, unit="", unit_price=0.0, total_price=None,
                 customer="", date=None, created=None, modified=None):

        # Генериране на UUID ако липсва
        self.invoice_id = str(invoice_id) if invoice_id else str(uuid.uuid4())

        # movement_id е UUID → пазим го като string
        self.movement_id = str(movement_id) if movement_id is not None else None

        self.product = product
        self.customer = customer
        self.quantity = round(float(quantity), 2)
        self.unit = unit
        self.unit_price = round(float(unit_price), 2)

        # Автоматично изчисляване на total_price ако не е подадено
        self.total_price = (
            round(self.quantity * self.unit_price, 2)
            if total_price is None else round(float(total_price), 2)
        )

        # Автоматично генериране на дата
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        # Валидация – подаваме всички 8 аргумента
        InvoiceValidator.validate_all(
            self.product,
            self.customer,
            self.quantity,
            self.unit,
            self.unit_price,
            self.movement_id,
            self.date,
            self.total_price
        )

    def to_dict(self):
        """Конвертирам към dict за JSON."""
        return {
            "invoice_id": self.invoice_id, "movement_id": self.movement_id,
            "product": self.product, "quantity": self.quantity,
            "unit": self.unit, "unit_price": self.unit_price,
            "total_price": self.total_price, "customer": self.customer,
            "date": self.date, "created": self.created, "modified": self.modified}

    @staticmethod
    def from_dict(data):
        """Създавам на Invoice от JSON речник."""
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
