import uuid
from datetime import datetime
from validators.invoice_validator import InvoiceValidator


class Invoice:
    """ Модел за фактура с истински UUID вместо авто-инкремент ID."""
    def __init__(self, invoice_id=None, movement_id=None, product="",
                 quantity=0, unit="", unit_price=0.0, total_price=None,
                 customer="", date=None, created=None, modified=None):

        # Ако ID липсва → генерираме нов UUID
        self.invoice_id = str(invoice_id) if invoice_id else str(uuid.uuid4())
        #  movement_id вече е UUID → пазим го като string, НЕ като int
        self.movement_id = str(movement_id) if movement_id is not None else None
        self.product = product
        self.quantity = round(float(quantity), 2)
        self.unit = unit
        self.unit_price = round(float(unit_price), 2)
        # total_price може да е подадено или да се изчисли
        self.total_price = round(self.quantity * self.unit_price, 2) \
            if total_price is None else round(float(total_price), 2)
        self.customer = customer
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        # Валидация
        InvoiceValidator.validate_all(self.product, self.customer, self.quantity, self.unit, self.unit_price,
                                      self.movement_id)


    def to_dict(self):
        """Конвертиране към dict за JSON."""
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
        """Създаване на Invoice от JSON речник."""
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
