import uuid
from datetime import datetime


class Invoice:
    @staticmethod
    def generate_id():
        return str(uuid.uuid4())

    @staticmethod
    def now():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def __init__(self, product, quantity, unit, unit_price, total_price, customer,
                 movement_id=None, date=None, created=None, modified=None,
                 invoice_id=None, is_active=True):

        # Идентификатори
        if invoice_id:
            self.invoice_id = str(invoice_id)
        else:
            self.invoice_id = Invoice.generate_id()

        self.movement_id = str(movement_id) if movement_id else None

        # Данни за сделката
        self.product = product
        self.customer = customer
        self.quantity = float(quantity)
        self.unit = unit
        self.unit_price = float(unit_price)
        self.total_price = float(total_price)

        # СТАТУС (Soft Delete флаг)
        # True означава валидна фактура, False означава анулирана ("нулена")
        self.is_active = bool(is_active)

        # Дати и време
        now_val = Invoice.now()
        self.date = date if date else now_val
        self.created = created if created else now_val
        self.modified = modified if modified else now_val

    def update_modified(self):
        """ Обновява времето на последна промяна. """
        self.modified = Invoice.now()

    def cancel(self):
        """ Анулира фактурата (променя статуса на неактивен). """
        self.is_active = False
        self.update_modified()

    def to_dict(self):
        """ Превръща обекта в речник за запис в JSON/База данни. """
        return {
            "invoice_id": self.invoice_id,
            "movement_id": self.movement_id,
            "product": self.product,
            "quantity": self.quantity,
            "unit": self.unit,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "customer": self.customer,
            "is_active": self.is_active,  # Важно за запазване на статуса
            "date": self.date,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        """ Създава обект Invoice от речник. """
        if not data:
            return None

        return Invoice(
            invoice_id=data.get("invoice_id"),
            movement_id=data.get("movement_id"),
            product=data.get("product", "Неизвестен"),
            quantity=data.get("quantity", 0),
            unit=data.get("unit", "бр."),
            unit_price=data.get("unit_price", 0.0),
            total_price=data.get("total_price", 0.0),
            customer=data.get("customer", "Неизвестен"),
            is_active=data.get("is_active", True), # Зареждаме статуса
            date=data.get("date"),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        short_id = self.invoice_id[:8]
        status = "ВАЛИДНА" if self.is_active else "АНУЛИРАНА"
        return f"Фактура #{short_id} [{status}] | Клиент: {self.customer} | Общо: {self.total_price:.2f} лв."