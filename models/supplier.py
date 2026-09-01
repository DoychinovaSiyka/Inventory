import uuid
from datetime import datetime






class Supplier:
    def __init__(self, supplier_id=None, name="", contact="", address="", created=None, modified=None):
        if supplier_id:
            self.supplier_id = str(supplier_id)
        else:
            self.supplier_id = str(uuid.uuid4())


        self.name = str(name).strip()
        self.contact = str(contact).strip()
        self.address = str(address).strip()


        now_val = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(created, str):
            self.created = created
        else:
            self.created = now_val

        if isinstance(modified, str):
            self.modified = modified
        else:
            self.modified = now_val






    def update_modified(self):
        self.modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



    def to_dict(self):
        return {"supplier_id": self.supplier_id, "name": self.name,
                "contact": self.contact, "address": self.address,
                "created": self.created, "modified": self.modified}



    @staticmethod
    def from_dict(d):
        if not d:
            return None

        return Supplier(supplier_id=d.get("supplier_id"), name=d.get("name", ""), contact=d.get("contact", ""),
                        address=d.get("address", ""), created=d.get("created"), modified=d.get("modified"))



    def __str__(self):
        short_id = self.supplier_id[:8]
        return f"Доставчик: {self.name} [ID: {short_id}] | Контакт: {self.contact}"
