from typing import Optional, List
from datetime import datetime
import uuid
from models.supplier import Supplier
from validators.supplier_validator import SupplierValidator


class SupplierController:
    """ Контролер за доставчици. Координира валидатор, модел и хранилище. Не съдържа бизнес логика."""
    def __init__(self, repo):
        self.repo = repo
        self.suppliers: List[Supplier] = [Supplier.from_dict(s) for s in self.repo.load()]

    # INTERNAL HELPERS
    @staticmethod
    def _now() -> str:
        """Връща текущата дата и час в стандартен формат."""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # CREATE
    def add(self, name: str, contact: str, address: str) -> Supplier:
        """ Добавя нов доставчик след пълна валидация. Контролерът не валидира сам – използва SupplierValidator."""

        SupplierValidator.validate_all(name, contact, address)
        now = self._now()
        supplier = Supplier(supplier_id=str(uuid.uuid4()), name=name.strip(),
                            contact=contact.strip(), address=address.strip(), created=now, modified=now)
        self.suppliers.append(supplier)
        self.save_changes()
        return supplier

    # READ
    def get_all(self) -> List[Supplier]:
        """Връща всички доставчици."""
        return self.suppliers

    def get_by_id(self, supplier_id: str) -> Optional[Supplier]:
        """Намира доставчик по ID."""
        sid = str(supplier_id)
        return next((s for s in self.suppliers if s.supplier_id == sid), None)


    def update(self, supplier_id: str, name: Optional[str] = None, contact: Optional[str] = None,
               address: Optional[str] = None) -> Supplier:
        """ Актуализира доставчик след валидация на подадените полета. """
        supplier = SupplierValidator.validate_exists(supplier_id, self)
        if name is not None:
            SupplierValidator.validate_name(name)
            supplier.name = name.strip()
        if contact is not None:
            SupplierValidator.validate_contact(contact)
            supplier.contact = contact.strip()
        if address is not None:
            SupplierValidator.validate_address(address)
            supplier.address = address.strip()
        supplier.modified = self._now()
        self.save_changes()
        return supplier


    def remove(self, supplier_id: str) -> bool:
        """ Изтрива доставчик след проверка за съществуване."""
        SupplierValidator.validate_exists(supplier_id, self)
        supplier = self.get_by_id(supplier_id)
        self.suppliers.remove(supplier)
        self.save_changes()
        return True

    def save_changes(self) -> None:
        """Записва всички доставчици в JSON хранилището."""
        self.repo.save([s.to_dict() for s in self.suppliers])
