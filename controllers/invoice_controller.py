from typing import List, Optional
from models.invoice import Invoice
from validators.invoice_validator import InvoiceValidator
from filters.invoice_filters import (filter_by_customer, filter_by_product, filter_by_date,
                                     filter_by_total_range, filter_by_date_range, filter_advanced)


class InvoiceController:
    """Контролерът се грижи за CRUD операциите и координацията между слоевете."""

    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller

        # Зареждане на фактурите
        raw = self.repo.load() or []
        self.invoices: List[Invoice] = [Invoice.from_dict(inv) for inv in raw]

    def _save_changes(self):
        self.repo.save([inv.to_dict() for inv in self.invoices])

    def _log(self, user_id: str, action: str, message: str):
        if self.activity_log:
            self.activity_log.log_action(user_id, action, message)

    # СЪЗДАВАНЕ НА ФАКТУРА
    def add(self, invoice_data: dict, user_id: str) -> Invoice:
        InvoiceValidator.validate_all(**invoice_data)

        invoice = Invoice(**invoice_data)
        self.invoices.append(invoice)
        self._save_changes()

        self._log(user_id, "GENERATE_INVOICE",
                  f"Ръчно генерирана фактура #{invoice.invoice_id[:8]} за {invoice.customer}")
        return invoice

    # АВТОМАТИЧНА ФАКТУРА ОТ OUT ДВИЖЕНИЕ
    def create_from_movement(self, movement, product, customer: str, user_id: str) -> Invoice:
        qty = float(movement.quantity)
        unit_price = float(movement.price)
        total_price = round(qty * unit_price, 2)

        invoice = Invoice(product=product.name, quantity=qty, unit=movement.unit, unit_price=unit_price,
                          total_price=total_price, customer=customer, movement_id=movement.movement_id,
                          date=movement.date, created=movement.date, modified=movement.date, invoice_id=None)

        self.invoices.append(invoice)
        self._save_changes()

        self._log(user_id, "GENERATE_INVOICE",
                  f"Автоматична фактура #{invoice.invoice_id[:8]} за движение {movement.movement_id[:8]}")

        return invoice

    def get_all(self) -> List[Invoice]:
        return self.invoices

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """ Търсим по префикс. Позволява на потребителя да въведе само първите 8 символа."""
        target_id = str(invoice_id).strip()
        if not target_id:
            return None

        for inv in self.invoices:
            if inv.invoice_id.startswith(target_id):
                return inv
        return None

    def update_customer(self, invoice_id: str, new_customer: str, user_id: str) -> bool:
        inv = self.get_by_id(invoice_id)
        if not inv:
            raise ValueError("Фактурата не е намерена.")

        InvoiceValidator.validate_customer(new_customer)
        inv.customer = new_customer
        inv.update_modified()
        self._save_changes()

        self._log(user_id, "EDIT_INVOICE", f"Променен клиент на фактура {inv.invoice_id[:8]}")
        return True

    def remove(self, invoice_id: str, user_id: str) -> bool:
        inv = self.get_by_id(invoice_id)
        if not inv:
            return False

        full_id = inv.invoice_id
        before = len(self.invoices)
        self.invoices = [i for i in self.invoices if i.invoice_id != full_id]

        if len(self.invoices) < before:
            self._save_changes()
            self._log(user_id, "DELETE_INVOICE", f"Изтрита фактура {full_id[:8]}")
            return True
        return False

    # ФИЛТРИ И ТЪРСЕНЕ
    def search_by_customer(self, keyword: str):
        return filter_by_customer(self.invoices, keyword)

    def search_by_product(self, keyword: str):
        return filter_by_product(self.invoices, keyword)

    def search_by_date(self, date_str: str):
        InvoiceValidator.validate_date(date_str)
        return filter_by_date(self.invoices, date_str)

    def search_by_total(self, min_total=None, max_total=None):
        return filter_by_total_range(self.invoices, min_total, max_total)

    def advanced_search(self, **kwargs):
        InvoiceValidator.validate_search_filters(kwargs.get("start_date"),
                                                 kwargs.get("end_date"), kwargs.get("min_total"),
                                                 kwargs.get("max_total"))
        return filter_advanced(self.invoices, **kwargs)