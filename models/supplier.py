import uuid
from datetime import datetime


class Supplier:
    def __init__(self, supplier_id=None, name="", contact="", address="", created=None, modified=None):


        if not supplier_id:
            self.supplier_id = str(uuid.uuid4())
        else:
            self.supplier_id = str(supplier_id)

        self.name = str(name).strip()
        self.contact = str(contact).strip()
        self.address = str(address).strip()

        now_val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created or now_val
        self.modified = modified or now_val

    def update_modified(self):
        """Обновява времето на последна промяна."""
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        """Превръща обекта в речник за JSON (записва пълното ID)."""
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "contact": self.contact,
            "address": self.address,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(d):
        """Зарежда обекта от JSON речник."""
        if not d:
            return None
        return Supplier(
            supplier_id=d.get("supplier_id"),
            name=d.get("name", ""),
            contact=d.get("contact", ""),
            address=d.get("address", ""),
            created=d.get("created"),
            modified=d.get("modified")
        )

    def __str__(self):
        # 2. ВИЗУАЛИЗАЦИЯ: Режем до 8 символа само при принтиране в терминала
        short_id = self.supplier_id[:8]
        return f"Доставчик: {self.name} [ID: {short_id}] | Контакт: {self.contact}"