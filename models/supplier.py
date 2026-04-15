class Supplier:
    def __init__(self, supplier_id, name, contact, address, created, modified):
        """ Модел за доставчик. Датите (created/modified) идват от контролера."""
        self.supplier_id = str(supplier_id)
        self.name = str(name).strip()
        self.contact = str(contact).strip()
        self.address = str(address).strip()
        self.created = created
        self.modified = modified

    def to_dict(self):
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
        return f"Доставчик: {self.name} | Контакт: {self.contact}"
