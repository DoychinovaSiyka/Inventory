from typing import Optional, List
from models.supplier import Supplier
from validators.supplier_validator import SupplierValidator


class SupplierController:
    """Контролерът управлява доставчиците и координира валидатора, модела и хранилището."""

    def __init__(self, repo):
        self.repo = repo
        # Зареждаме съществуващите данни от репозиториума
        data = self.repo.load() or []
        self.suppliers: List[Supplier] = [Supplier.from_dict(s) for s in data]

    # CREATE
    def add(self, name: str, contact: str, address: str) -> Supplier:
        """ Добавя нов доставчик след пълна валидация. Контролерът не валидира сам – използва SupplierValidator. """
        SupplierValidator.validate_all(name, contact, address)

        supplier = Supplier(name=name.strip(), contact=contact.strip(), address=address.strip())
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
        for supplier in self.suppliers:
            if supplier.supplier_id == sid:
                return supplier
        return None

    # UPDATE
    def update(self, supplier_id: str, name: Optional[str] = None,
               contact: Optional[str] = None, address: Optional[str] = None) -> Supplier:
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

        # Обновявам датата на промяна чрез модела
        supplier.update_modified()

        self.save_changes()
        return supplier

    # DELETE
    def remove(self, supplier_id: str) -> bool:
        """ Изтрива доставчик след проверка за съществуване. """
        SupplierValidator.validate_exists(supplier_id, self)
        supplier = self.get_by_id(supplier_id)
        if supplier:
            self.suppliers.remove(supplier)
            self.save_changes()
            return True
        return False

    def save_changes(self) -> None:
        """Записва всички доставчици в JSON хранилището."""
        self.repo.save([s.to_dict() for s in self.suppliers])