from models.supplier import Supplier
from validators.suplier_validator import SupplierValidator
from datetime import datetime


class SupplierController:
    def __init__(self,repo):
        self.repo = repo
        self.suppliers = [Suplier.from_dict(s) for s in self.repo.load()]

    # INTERNAL: ID GENERATOR
    def _generate_id(self):
        if not self.suppliers:
            return 1
        return max(s.suplier_id for s in self.suppliers) + 1

    # CREATE
    def add(self,name,contact,address):
        SupplierValidator.validate_all(name,contact,address)

        new_id = self._generate_id()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        supplier = Supplier(
            supplier_id= new_id,
            name = name,
            contact = contact,
            address = address,
            created = now,
            modified = now

        )

        self.suppliers.append(supplier)
        self._save()
        return supplier


    # READ
    def get_all(self):
        return self.suppliers

    def get_by_id(self, supplier_id):
        for s in self.suppliers:
            if s.suplier_id == supplier_id:
                return s
        return None

    # READ
    def update(self, supplier_id, name=None, contact=None, address=None):
        s = self.get_by_id(supplier_id)
        if not s:
            raise ValueError("Доставчикът  не е намерена.")


        if name is not None:
            SupplierValidator.validate_name(name)
            s.name = name
        if contact is not None:
            SupplierValidator.validate_contact(contact)
            s.contact = contact
        if address is not None:
            SupplierValidator.validate_address(address)
            s.address = address

        s.modified = str(datetime.now())
        self._save()
        return s

        # DELETE

    def remove(self, supplier_id):
        s = self.get_by_id(supplier_id)
        if not s:
            return False
        self.suppliers.remove(s)
        self._save()
        return True

    # save to JSON

    def _save(self):
        self.repo.save([s.to_dict() for s in self.suppliers])



