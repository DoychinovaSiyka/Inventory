from typing import Optional, List
from models.supplier import Supplier
from validators.supplier_validator import SupplierValidator



class SupplierController:
    """Контролерът управлява доставчиците и координира валидатора, модела и хранилището."""
    def __init__(self, repo):
        self.repo = repo
        data = self.repo.load() or []
        self.suppliers: List[Supplier] = [Supplier.from_dict(s) for s in data]

    def add(self, name: str, contact: str, address: str) -> Supplier:
        SupplierValidator.validate_all(name, contact, address)

        supplier = Supplier(supplier_id=None, name=name.strip(), contact=contact.strip(), address=address.strip())
        self.suppliers.append(supplier)
        self.save_changes()
        return supplier


    # READ
    def get_all(self) -> List[Supplier]:
        return self.suppliers

    def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        sid = str(supplier_id).strip()
        if not sid:
            return None

        for supplier in self.suppliers:
            if supplier.supplier_id.startswith(sid):
                return supplier
        return None

    def update(self, supplier_id: str, name: Optional[str] = None,
               contact: Optional[str] = None, address: Optional[str] = None) -> Supplier:

        supplier = self.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")

        if name is not None:
            SupplierValidator.validate_name(name)
            supplier.name = name.strip()
        if contact is not None:
            SupplierValidator.validate_contact(contact)
            supplier.contact = contact.strip()
        if address is not None:
            SupplierValidator.validate_address(address)
            supplier.address = address.strip()

        supplier.update_modified()
        self.save_changes()
        return supplier



    def remove(self, supplier_id: str) -> bool:
        supplier = self.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")

        self.suppliers.remove(supplier)
        self.save_changes()
        return True


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



    def save_changes(self) -> None:
        self.repo.save([s.to_dict() for s in self.suppliers])
