import uuid
from datetime import datetime




class Invoice:
    def __init__(self, product, quantity, unit, unit_price, total_price, customer,
                 movement_id=None, date=None, created=None, modified=None, invoice_id=None, status=True):


        if invoice_id:
            self.invoice_id = str(invoice_id)
        else:
            self.invoice_id = str(uuid.uuid4())


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
        self.is_active = bool(status)


        now_val = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if isinstance(date, str):
            self.date = date
        else:
            self.date = now_val

        if isinstance(created, str):
            self.created = created
        else:
            self.created = now_val

        if isinstance(modified, str):
            self.modified = modified
        else:
            self.modified = now_val






    def cancel(self):
        self.is_active = False
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')




    def to_dict(self):
        return {"invoice_id": self.invoice_id, "movement_id": self.movement_id, "product": self.product,
                "quantity": self.quantity, "unit": self.unit, "unit_price": self.unit_price,
                "total_price": self.total_price, "customer": self.customer,
                "is_active": self.is_active, "date": self.date, "created": self.created, "modified": self.modified}




    @staticmethod
    def from_dict(data):
        if not data:
            return None

        return Invoice(invoice_id=data.get("invoice_id"), movement_id=data.get("movement_id"),
                       product=data.get("product", "Неизвестен"), quantity=data.get("quantity", 0),
                       unit=data.get("unit", "бр."), unit_price=data.get("unit_price", 0.0),
                       total_price=data.get("total_price", 0.0), customer=data.get("customer", "Неизвестен"),
                       status=data.get("is_active", True), date=data.get("date"), created=data.get("created"),
                       modified=data.get("modified"))




    def __str__(self):
        short_id = self.invoice_id[:8]
        status = "ВАЛИДНА" if self.is_active else "АНУЛИРАНА"
        return f"Фактура {short_id} [{status}] | Клиент: {self.customer} | Общо: {self.total_price:.2f} лв."
