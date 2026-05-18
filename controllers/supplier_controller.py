from typing import Optional, List
from models.supplier import Supplier
from validators.supplier_validator import SupplierValidator
from controllers.abstract_controller import AbstractController


class SupplierController(AbstractController):
    """Управлява доставчиците в системата."""

    def __init__(self, repo):
        super().__init__(repo)
        self.suppliers = self.load() or []


    def from_dict(self, data):
        return Supplier.from_dict(data)

    def to_dict(self, obj):
        return obj.to_dict()

    def save_suppliers(self):
        self.save(self.suppliers)


    def add(self, name: str, contact: str, address: str) -> Supplier:
        SupplierValidator.validate_name(name)
        SupplierValidator.validate_contact(contact)
        SupplierValidator.validate_address(address)
        SupplierValidator.validate_unique_name(name, self.suppliers)

        supplier = Supplier(name=name, contact=contact, address=address)
        self.suppliers.append(supplier)
        self.save_suppliers()
        return supplier

    def update(self, supplier_id: str, name=None, contact=None, address=None) -> bool:
        supplier = self.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Доставчикът не е намерен.")

        if name is not None:
            SupplierValidator.validate_name(name)
            SupplierValidator.validate_unique_name(name, self.suppliers, exclude_id=supplier.supplier_id)
            supplier.name = name.strip()
        if contact is not None:
            supplier.contact = SupplierValidator.validate_contact(contact)
        if address is not None:
            supplier.address = SupplierValidator.validate_address(address)

        supplier.update_modified()
        self.save_suppliers()
        return True



    def get_by_id(self, identifier: str) -> Optional[Supplier]:
        sid = str(identifier).strip().lower()
        for s in self.suppliers:
            if s.supplier_id.lower() == sid or s.supplier_id[:8].lower() == sid:
                return s
        return None

    def get_all(self) -> List[Supplier]:
        return self.suppliers


    def search(self, query: str) -> List[Supplier]:
        q = str(query).strip().lower()
        return [s for s in self.suppliers if q in s.name.lower() or q in s.supplier_id[:8].lower()]



    def remove(self, supplier_id: str) -> bool:
        supplier = self.get_by_id(supplier_id)
        if supplier:
            self.suppliers.remove(supplier)
            self.save_suppliers()
            return True
        return False


    def validate_field(self, field_type: str, value: str) -> Optional[str]:
        try:
            if field_type == "name":
                SupplierValidator.validate_name(value)
            elif field_type == "contact":
                SupplierValidator.validate_contact(value)
            elif field_type == "address":
                SupplierValidator.validate_address(value)
            return None
        except ValueError as e:
            return str(e)


