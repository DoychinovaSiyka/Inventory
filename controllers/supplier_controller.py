from typing import Optional, List
from datetime import datetime
import uuid
from models.supplier import Supplier
from validators.supplier_validator import SupplierValidator


class SupplierController:
    def __init__(self, repo):
        self.repo = repo
        # Зареждаме доставчиците
        self.suppliers: List[Supplier] = [Supplier.from_dict(s) for s in self.repo.load()]

    # ID GENERATOR
    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    # CREATE
    def add(self, name: str, contact: str, address: str) -> Supplier:
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
        self.save_changes()
        return supplier

    # READ
    def get_all(self) -> List[Supplier]:
        return self.suppliers

    def get_by_id(self, supplier_id: str) -> Supplier:
        supplier = next((s for s in self.suppliers if s.supplier_id == supplier_id), None)
        if not supplier:
            raise ValueError(f"Доставчик с ID {supplier_id} не съществува.")
        return supplier

    # UPDATE
    def update(self, supplier_id: str, name: Optional[str] = None,
               contact: Optional[str] = None, address: Optional[str] = None) -> Supplier:

        supplier = self.get_by_id(supplier_id)

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
        self.save_changes()
        return supplier

    # DELETE
    def remove(self, supplier_id: str) -> bool:
        supplier = self.get_by_id(supplier_id)
        self.suppliers.remove(supplier)
        self.save_changes()
        return True

    # SAVE
    def save_changes(self) -> None:
        self.repo.save([s.to_dict() for s in self.suppliers])
