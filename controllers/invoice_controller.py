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

    #  INTERNAL HELPERS

    @staticmethod
    def _generate_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _load_invoices(self):
        raw_data = self.repo.load() or []
        self.invoices = [Invoice.from_dict(inv) for inv in raw_data]

    def _log(self, user_id: str, action: str, message: str):
        if self.activity_log:
            self.activity_log.add_log(user_id, action, message)

    # CREATE

    def add(self, invoice_data: dict, user_id: str) -> Invoice:
        InvoiceValidator.validate_all(**invoice_data)

        now = self._now()
        invoice = Invoice(invoice_id=self._generate_id(), **invoice_data, created=now, modified=now)
        self.invoices.append(invoice)
        self._save_changes()
        self._log(user_id, "GENERATE_INVOICE", f"Ръчно генерирана фактура за {invoice.customer}")
        return invoice

    def create_from_movement(self, movement, product, customer: str, user_id: str) -> Invoice:
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
        self._log(user_id, "GENERATE_INVOICE", f"Автоматична фактура за движение {movement.movement_id}")
        return invoice

    # READ / SEARCH
    def get_all(self) -> List[Invoice]:
        return self.invoices

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        invoice_id = invoice_id.strip()
        return next((inv for inv in self.invoices if inv.invoice_id == invoice_id), None)

    # Търсене по клиент - частично
    def search_by_customer(self, keyword: str) -> List[Invoice]:
        if not keyword.strip():
            return []
        keyword = keyword.lower().strip()
        return [inv for inv in self.invoices if keyword in inv.customer.lower()]


    def search_by_product(self, keyword: str) -> List[Invoice]:
        if not keyword.strip():
            return []
        keyword = keyword.lower().strip()
        return [inv for inv in self.invoices if keyword in inv.product.lower()]

    # Търсене по дата с валидиране
    def search_by_date(self, date_str: str):
        date_str = date_str.strip()
        if len(date_str) != 10 or date_str.count("-") != 2:
            return "INVALID_FORMAT"
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return "INVALID_DATE"

        # Филтриране
        return [inv for inv in self.invoices if inv.date.startswith(date_str)]

    #  Търсене по сума
    def search_by_total(self, min_total=None, max_total=None) -> List[Invoice]:
        min_val = InvoiceValidator.parse_float(min_total, "Минимална сума") if min_total else None
        max_val = InvoiceValidator.parse_float(max_total, "Максимална сума") if max_total else None

        return [inv for inv in self.invoices if (min_val is None or inv.total_price >= min_val)
                and (max_val is None or inv.total_price <= max_val)]

    #  Разширено търсене
    def advanced_search(self, **kwargs) -> List[Invoice]:
        customer = kwargs.get("customer")
        product = kwargs.get("product")
        start_date = kwargs.get("start_date")
        end_date = kwargs.get("end_date")
        min_total = kwargs.get("min_total")
        max_total = kwargs.get("max_total")

        results = self.invoices

        if customer:
            customer = customer.lower()
            results = [inv for inv in results if customer in inv.customer.lower()]


        if product:
            product = product.lower()
            results = [inv for inv in results if product in inv.product.lower()]


        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                results = [inv for inv in results if datetime.strptime(inv.date[:10], "%Y-%m-%d") >= start]
            except ValueError:
                return "INVALID_START_DATE"

        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                results = [inv for inv in results if datetime.strptime(inv.date[:10], "%Y-%m-%d") <= end]
            except ValueError:
                return "INVALID_END_DATE"


        if min_total:
            try:
                min_val = float(min_total)
                results = [inv for inv in results if inv.total_price >= min_val]
            except ValueError:
                return "INVALID_MIN_TOTAL"


        if max_total:
            try:
                max_val = float(max_total)
                results = [inv for inv in results if inv.total_price <= max_val]
            except ValueError:
                return "INVALID_MAX_TOTAL"

        return results


    def update_customer(self, invoice_id: str, new_customer: str, user_id: str) -> bool:
        inv = self.get_by_id(invoice_id)
        if not inv:
            raise ValueError("Фактурата не е намерена.")

        InvoiceValidator.validate_customer(new_customer)
        inv.customer = new_customer
        inv.update_modified()

        self._save_changes()
        self._log(user_id, "EDIT_INVOICE", f"Променен клиент на фактура {invoice_id}")
        return True


    def remove(self, invoice_id: str, user_id: str) -> bool:
        before = len(self.invoices)
        self.invoices = [inv for inv in self.invoices if inv.invoice_id != invoice_id]

        if len(self.invoices) < before:
            self._save_changes()
            self._log(user_id, "DELETE_INVOICE", f"Изтрита фактура {invoice_id}")
            return True

        return False


    def _save_changes(self) -> None:
        self.repo.save([inv.to_dict() for inv in self.invoices])
