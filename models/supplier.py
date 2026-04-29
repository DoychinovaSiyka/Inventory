import uuid
from datetime import datetime


class Supplier:
    def __init__(self, supplier_id=None, name="", contact="", address="", created=None, modified=None):
        """ Модел за доставчик. Датите (created/modified) идват от контролера. """


        self.supplier_id = str(supplier_id) if supplier_id else str(uuid.uuid4())
        self.name = str(name).strip()
        self.contact = str(contact).strip()
        self.address = str(address).strip()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        """Обновявам датата при промяна на обекта."""
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self):
        return {"supplier_id": self.supplier_id, "name": self.name,
                "contact": self.contact, "address": self.address,
                "created": self.created, "modified": self.modified}


    @staticmethod
    def from_dict(d):
        if not d:
            return None
        return Supplier(supplier_id=d.get("supplier_id"), name=d.get("name", ""),
                        contact=d.get("contact", ""), address=d.get("address", ""),
                        created=d.get("created"), modified=d.get("modified"))

    def __str__(self):
        return f"Доставчик: {self.name} | Контакт: {self.contact}"