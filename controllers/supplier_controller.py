from typing import Optional, List
from datetime import datetime
import uuid
from models.supplier import Supplier
from validators.supplier_validator import SupplierValidator


class SupplierController:
    def __init__(self, repo):
        self.repo = repo
        self.suppliers: List[Supplier] = [Supplier.from_dict(s) for s in self.repo.load()]

    def _get_now(self) -> str:
        """ Помощен метод за централизирано време. """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # CREATE
    def add(self, name: str, contact: str, address: str) -> Supplier:
        SupplierValidator.validate_all(name, contact, address)

        now = self._get_now()
        supplier = Supplier(
            supplier_id=str(uuid.uuid4()),
            name=name.strip(),
            contact=contact.strip(),
            address=address.strip(),
            created=now,
            modified=now
        )

        self.suppliers.append(supplier)
        self.save_changes()
        return supplier

    # READ
    def get_all(self) -> List[Supplier]:
        return self.suppliers

    def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        sid = str(supplier_id)
        return next((s for s in self.suppliers if s.supplier_id == sid), None)


    def update(self, supplier_id: str, name: Optional[str] = None,
               contact: Optional[str] = None, address: Optional[str] = None) -> Supplier:

        supplier = self.get_by_id(supplier_id)
        if not supplier:
            raise ValueError(f"Доставчик с ID {supplier_id} не е намерен.")

        if name is not None:
            SupplierValidator.validate_name(name)
            supplier.name = name.strip()

        if contact is not None:
            SupplierValidator.validate_contact(contact)
            supplier.contact = contact.strip()

        if address is not None:
            SupplierValidator.validate_address(address)
            supplier.address = address.strip()

        supplier.modified = self._get_now()
        self.save_changes()
        return supplier


    def remove(self, supplier_id: str) -> bool:
        supplier = self.get_by_id(supplier_id)
        if supplier:
            self.suppliers.remove(supplier)
            self.save_changes()
            return True
        return False

    def save_changes(self) -> None:
        self.repo.save([s.to_dict() for s in self.suppliers])
