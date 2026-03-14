from datetime import datetime


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
        self.quantity = quantity
        self.unit = unit
        self.unit_price = unit_price

        # ако не е подадена обща цена - изчисляваме я
        self.total_price = total_price if total_price is not None else quantity * unit_price

        self.customer = customer

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        self.validate()

    def assign_new_id(self, existing_items):
        # извиква се от контролера, ако id липсва
        if self.invoice_id is None:
            self.invoice_id = generate_next_invoice_id(existing_items)

    def validate(self):
        if not self.product:
            raise ValueError("продуктът е задължителен.")

        if not self.customer:
            raise ValueError("клиентът е задължителен.")

        if self.quantity <= 0:
            raise ValueError("quantity трябва да е > 0.")

        if not self.unit or not self.unit.strip():
            raise ValueError("мерната единица е задължителна.")

        if self.unit_price <= 0:
            raise ValueError("unit price трябва да е > 0.")

        if self.movement_id is None:
            raise ValueError("movement_id е задължителен.")

    def to_dict(self):
        # конвертиране към dict за json
        return {"invoice_id": self.invoice_id,
            "movement_id": self.movement_id,"product": self.product,"quantity": self.quantity,
            "unit": self.unit,"unit_price": self.unit_price,
            "total_price": self.total_price,
            "customer": self.customer,"date": self.date,"created": self.created,
            "modified": self.modified}

    @staticmethod
    def from_dict(data):
        # създаване на invoice от json речник
        return Invoice( invoice_id=data.get("invoice_id"),movement_id=data.get("movement_id"),
            product=data.get("product"),quantity=data.get("quantity"),
            unit=data.get("unit", "бр."),unit_price=data.get("unit_price"),
            total_price=data.get("total_price"),customer=data.get("customer"),
            date=data.get("date"),created=data.get("created"),modified=data.get("modified"))
