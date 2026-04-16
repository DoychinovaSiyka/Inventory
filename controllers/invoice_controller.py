import uuid
from typing import Optional, List
from datetime import datetime
from storage.json_repository import JSONRepository
from models.invoice import Invoice
from validators.invoice_validator import InvoiceValidator
from filters.invoice_filters import (filter_by_customer, filter_by_product, filter_by_date,
                                     filter_by_total_range, filter_advanced)


class InvoiceController:
    """ Контролерът управлява фактурите, без да съдържа бизнес логика. """
    def __init__(self, repo: JSONRepository, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller
        self.invoices: List[Invoice] = []
        self._load_invoices()

    # INTERNAL HELPERS
    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _load_invoices(self):
        """ Зарежда данните през модела. """
        raw_data = self.repo.load() or []
        self.invoices = [Invoice.from_dict(inv) for inv in raw_data]

    def _log(self, user_id: str, action: str, message: str):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    # CREATE
    def add(self, invoice_data: dict, user_id: str) -> Invoice:
        """ Добавя готова фактура от речник. """
        InvoiceValidator.validate_all(**invoice_data)

        now = self._now()
        invoice = Invoice(invoice_id=self._generate_id(), **invoice_data, created=now, modified=now)
        self.invoices.append(invoice)
        self._save_changes()
        self._log(user_id, "GENERATE_INVOICE",
                  f"Ръчно генерирана фактура за {invoice.customer}")

        return invoice

    def create_from_movement(self, movement, product, customer: str, user_id: str) -> Invoice:
        """ Генерира фактура автоматично от стоково движение. """
        InvoiceValidator.validate_movement_for_invoice(movement)

        qty = float(movement.quantity)
        unit_price = round(float(movement.price), 2)
        total_price = round(qty * unit_price, 2)
        now = self._now()
        invoice = Invoice(invoice_id=self._generate_id(), movement_id=movement.movement_id,
                          product=product.name, quantity=qty, unit=movement.unit, unit_price=unit_price,
                          total_price=total_price, customer=customer, date=now, created=now, modified=now)

        self.invoices.append(invoice)
        self._save_changes()
        self._log(user_id, "GENERATE_INVOICE",
                  f"Автоматична фактура за движение {movement.movement_id}")

        return invoice

    # READ / SEARCH
    def get_all(self) -> List[Invoice]:
        return self.invoices

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        return next((inv for inv in self.invoices if inv.invoice_id == invoice_id), None)

    def search_by_customer(self, keyword: str) -> List[Invoice]:
        return filter_by_customer(self.invoices, keyword)

    def search_by_product(self, keyword: str) -> List[Invoice]:
        return filter_by_product(self.invoices, keyword)

    def search_by_date(self, date_str: str):
        """ Търсене по дата чрез външен филтър. """
        return filter_by_date(self.invoices, date_str)

    def search_by_total(self, min_total=None, max_total=None) -> List[Invoice]:
        min_val = InvoiceValidator.parse_float(min_total, "Минимална сума") if min_total else None
        max_val = InvoiceValidator.parse_float(max_total, "Максимална сума") if max_total else None
        return filter_by_total_range(self.invoices, min_val, max_val)

    def advanced_search(self, **kwargs) -> List[Invoice]:
        return filter_advanced(self.invoices, **kwargs)

    # UPDATE
    def update_customer(self, invoice_id: str, new_customer: str, user_id: str) -> bool:
        inv = self.get_by_id(invoice_id)
        if not inv:
            raise ValueError("Фактурата не е намерена.")
        InvoiceValidator.validate_customer(new_customer)
        inv.customer = new_customer
        inv.update_modified()

        self._save_changes()
        self._log(user_id, "EDIT_INVOICE",
                  f"Променен клиент на фактура {invoice_id}")

        return True

    # DELETE
    def remove(self, invoice_id: str, user_id: str) -> bool:
        before = len(self.invoices)
        self.invoices = [inv for inv in self.invoices if inv.invoice_id != invoice_id]
        if len(self.invoices) < before:
            self._save_changes()
            self._log(user_id, "DELETE_INVOICE",
                      f"Изтрита фактура {invoice_id}")
            return True

        return False

    # SAVE
    def _save_changes(self) -> None:
        self.repo.save([inv.to_dict() for inv in self.invoices])
