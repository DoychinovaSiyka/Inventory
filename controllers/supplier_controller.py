from models.supplier import Supplier
from validators.supplier_validator import SupplierValidator
from datetime import datetime


class SupplierController:
    def __init__(self, repo):
        self.repo = repo
        self.suppliers = [Supplier.from_dict(s) for s in self.repo.load()]

    # ---------------------------------------------------------
    # ID GENERATOR
    # ---------------------------------------------------------
    def _generate_id(self):
        if not self.suppliers:
            return 1
        return max(s.supplier_id for s in self.suppliers) + 1

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    def add(self, name, contact, address):
        SupplierValidator.validate_all(name, contact, address)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        supplier = Supplier(
            supplier_id=self._generate_id(),
            name=name,
            contact=contact,
            address=address,
            created=now,
            modified=now
        )

        self.suppliers.append(supplier)
        self._save()
        return supplier

    # ---------------------------------------------------------
    # READ
    # ---------------------------------------------------------
    def get_all(self):
        return self.suppliers

    def get_by_id(self, supplier_id):
        return next((s for s in self.suppliers if s.supplier_id == supplier_id), None)

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update(self, supplier_id, name=None, contact=None, address=None):
        supplier = self.get_by_id(supplier_id)
        if not supplier:
            raise ValueError("Доставчикът не е намерен.")

        if name is not None:
            SupplierValidator.validate_name(name)
            supplier.name = name

        if contact is not None:
            SupplierValidator.validate_contact(contact)
            supplier.contact = contact

        if address is not None:
            SupplierValidator.validate_address(address)
            supplier.address = address

        supplier.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save()
        return supplier

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------
    def remove(self, supplier_id):
        original_len = len(self.suppliers)
        self.suppliers = [s for s in self.suppliers if s.supplier_id != supplier_id]

        if len(self.suppliers) < original_len:
            self._save()
            return True
        return False

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------
    def _save(self):
        self.repo.save([s.to_dict() for s in self.suppliers])
