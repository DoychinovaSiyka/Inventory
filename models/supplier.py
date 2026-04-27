import uuid
from datetime import datetime


class Supplier:

    def __init__(self, supplier_id, name, contact, address, created=None, modified=None):
        """Модел за доставчик. Тук държа само данните и логиката за ID и датите."""

        # Ако няма подадено ID – генерирам ново
        self.supplier_id = str(supplier_id) if supplier_id else Supplier.generate_id()

        # Основни данни за доставчика
        self.name = str(name).strip()
        self.contact = str(contact).strip()
        self.address = str(address).strip()

        # Дати за създаване и промяна
        now = Supplier.now()
        self.created = created or now
        self.modified = modified or now

    # Генерираме ново ID за доставчик
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    # Връщам текущия момент като текст
    @staticmethod
    def now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_modified(self):
        """Обновявам датата при промяна на доставчика."""
        self.modified = Supplier.now()

    def to_dict(self):
        return {"supplier_id": self.supplier_id, "name": self.name,
                "contact": self.contact, "address": self.address,
                "created": self.created, "modified": self.modified}

    @staticmethod
    def from_dict(d):
        """Създавам Supplier от JSON речник."""
        if not d:
            return None
        return Supplier(supplier_id=d.get("supplier_id"), name=d.get("name", ""),
                        contact=d.get("contact", ""), address=d.get("address", ""),
                        created=d.get("created"), modified=d.get("modified"))

    def __str__(self):
        return f"Доставчик: {self.name} | Контакт: {self.contact}"
