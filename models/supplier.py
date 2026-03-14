import uuid
from datetime import datetime

class Supplier:
    def __init__(self, name, contact, address, supplier_id=None, created=None, modified=None):
        # Ако няма подадено ID - генерираме UUID
        self.supplier_id = supplier_id or str(uuid.uuid4())

        self.name = name.strip().title()
        self.contact = contact.strip()
        self.address = address.strip()

        self.created = created or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.modified = modified or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        return {
            "supplier_id": self.supplier_id,
            "name": self.name,
            "contact": self.contact,
            "address": self.address,
            "created": self.created,
            "modified": self.modified,
        }

    @staticmethod
    def from_dict(data):
        return Supplier( supplier_id=data.get("supplier_id"),
            name=data["name"],contact=data["contact"],
            address=data["address"],created=data.get("created"),
            modified=data.get("modified"))
