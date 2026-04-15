import uuid
from typing import Optional, List
from datetime import datetime
from storage.json_repository import JSONRepository
from models.invoice import Invoice
from validators.invoice_validator import InvoiceValidator

from filters.invoice_filters import (filter_by_customer, filter_by_product,
                                     filter_by_date, filter_by_total_range, filter_advanced)


class InvoiceController:
    def __init__(self, repo: JSONRepository, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller
        self.invoices: List[Invoice] = []
        self._load_invoices()

    def _load_invoices(self):
        """ Зарежда данните през модела. """
        raw_data = self.repo.load()
        self.invoices = [Invoice.from_dict(inv) for inv in raw_data]

    def _log(self, user_id, action, message):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)


    def add(self, invoice_data: dict, user_id: str) -> Invoice:
        """ Добавя готова фактура от речник. """
        InvoiceValidator.validate_all(**invoice_data)

        invoice = Invoice(invoice_id=str(uuid.uuid4()), **invoice_data,
                          created=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          modified=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        self.invoices.append(invoice)
        self.save_changes()
        self._log(user_id, "GENERATE_INVOICE", f"Ръчно генерирана фактура за {invoice.customer}")
        return invoice

    def create_from_movement(self, movement, product, customer: str, user_id: str) -> Invoice:
        """ Генерира фактура автоматично от стоково движение. """
        InvoiceValidator.validate_movement_for_invoice(movement)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        qty = float(movement.quantity)
        unit_price = round(float(movement.price), 2)
        total_price = round(qty * unit_price, 2)
        invoice = Invoice(
            invoice_id=str(uuid.uuid4()),
            movement_id=movement.movement_id,
            product=product.name,
            quantity=qty,
            unit=movement.unit,
            unit_price=unit_price,
            total_price=total_price,
            customer=customer,
            date=now,
            created=now,
            modified=now
        )

        self.invoices.append(invoice)
        self.save_changes()
        self._log(user_id, "GENERATE_INVOICE", f"Автоматична фактура за движение {movement.movement_id}")
        return invoice

    # READ / SEARCH
    def get_all(self) -> List[Invoice]:
        return self.invoices

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        return next((inv for inv in self.invoices if str(inv.invoice_id) == str(invoice_id)), None)

    def search_by_customer(self, keyword: str) -> List[Invoice]:
        return filter_by_customer(self.invoices, keyword)

    def search_by_product(self, keyword: str) -> List[Invoice]:
        """ Търсене по продукт чрез външен филтър (консистентно с архитектурата). """
        return filter_by_product(self.invoices, keyword)

    def search_by_date(self, date_str: str):
        """ Търсене по дата:
        - ако датата е невалидна → връща "INVALID_DATE"
        - ако е валидна → връща списък с фактури"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return "INVALID_DATE"

        results = []
        for inv in self.invoices:
            if inv.date.startswith(date_str):
                results.append(inv)

        return results

    def search_by_total(self, min_total: Optional[str] = None, max_total: Optional[str] = None) -> List[Invoice]:
        min_val = InvoiceValidator.parse_float(min_total, "Минимална сума") if min_total else None
        max_val = InvoiceValidator.parse_float(max_total, "Максимална сума") if max_total else None
        return filter_by_total_range(self.invoices, min_val, max_val)

    def advanced_search(self, **kwargs) -> List[Invoice]:
        return filter_advanced(self.invoices, **kwargs)


    def update_customer(self, invoice_id: str, new_customer: str, user_id: str) -> bool:
        inv = self.get_by_id(invoice_id)
        if not inv:
            raise ValueError("Фактурата не е намерена.")

        InvoiceValidator.validate_customer(new_customer)

        inv.customer = new_customer
        inv.update_modified()
        self.save_changes()
        self._log(user_id, "EDIT_INVOICE", f"Променен клиент на фактура {invoice_id}")
        return True


    def remove(self, invoice_id: str, user_id: str) -> bool:
        original_len = len(self.invoices)
        self.invoices = [inv for inv in self.invoices if str(inv.invoice_id) != str(invoice_id)]
        if len(self.invoices) < original_len:
            self.save_changes()
            self._log(user_id, "DELETE_INVOICE", f"Изтрита фактура {invoice_id}")
            return True
        return False


    def save_changes(self) -> None:
        self.repo.save([inv.to_dict() for inv in self.invoices])
