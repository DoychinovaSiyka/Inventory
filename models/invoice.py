from datetime import datetime


def generate_next_invoice_id(existing_items):
    if not existing_items:
        return 1
    try:
        ids = [int(item["invoice_id"]) for item in existing_items if "invoice_id" in item]
        return max(ids) + 1
    except:
        return 1


class Invoice:
    def __init__(self, invoice_id=None, movement_id=None, product="", quantity=0,
                 unit="", unit_price=0.0,
                 total_price=None, customer="", date=None, created=None, modified=None):

        # ID — AUTO-INCREMENT INT
        self.invoice_id = int(invoice_id) if invoice_id is not None else None

        # Movement → Invoice (1:1)
        self.movement_id = int(movement_id) if movement_id is not None else None

        self.product = product
        self.quantity = quantity
        self.unit = unit
        self.unit_price = unit_price
        self.total_price = total_price if total_price is not None else quantity * unit_price
        self.customer = customer

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.date = date or now
        self.created = created or now
        self.modified = modified or now

        self.validate()

    def assign_new_id(self, existing_items):
        """Извиква се от контролера, когато invoice_id е None."""
        if self.invoice_id is None:
            self.invoice_id = generate_next_invoice_id(existing_items)

    def validate(self):
        if not self.product:
            raise ValueError("Продуктът е задължителен (според SRS).")

        if not self.customer:
            raise ValueError("Клиентът е задължителен (според SRS).")

        if self.quantity <= 0:
            raise ValueError("Quantity трябва да е > 0 (според SRS).")

        if not self.unit or not self.unit.strip():
            raise ValueError("Мерната единица е задължителна (според SRS).")

        if self.unit_price <= 0:
            raise ValueError("Unit price трябва да е > 0 (според SRS).")

        if self.movement_id is None:
            raise ValueError("movement_id е задължителен (според SRS).")

    def to_dict(self):
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
