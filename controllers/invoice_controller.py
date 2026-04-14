from typing import Optional, List
from datetime import datetime
from models.invoice import Invoice
from storage.json_repository import JSONRepository
from validators.invoice_validator import InvoiceValidator

from filters.invoice_filters import (filter_by_customer, filter_by_product, filter_by_date,
                                     filter_by_total_range, filter_advanced)


class InvoiceController:
    def __init__(self, repo: JSONRepository, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller
        raw = self.repo.load()
        self.invoices: List[Invoice] = []

        # Зареждам фактурите от JSON. Ако някоя няма UUID – генерирам нов.
        for inv in raw:
            invoice = Invoice.from_dict(inv)
            self.invoices.append(invoice)

        self.save_changes()

    # CREATE
    def add(self, invoice: Invoice) -> Invoice:
        InvoiceValidator.validate_all(
            product=invoice.product,
            customer=invoice.customer,
            quantity=invoice.quantity,
            unit=invoice.unit,
            unit_price=invoice.unit_price,
            movement_id=invoice.movement_id,
            date=invoice.date,
            total_price=invoice.total_price
        )

        self.invoices.append(invoice)
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(invoice.customer, "GENERATE_INVOICE",
                                      f"Invoice created for movement {invoice.movement_id}")

        return invoice

    def create_from_movement(self, movement, product, customer: str) -> Invoice:
        InvoiceValidator.validate_movement_for_invoice(movement)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        qty = float(movement.quantity)
        unit_price = round(float(movement.price), 2)
        total_price = round(qty * unit_price, 2)

        invoice = Invoice(
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

        InvoiceValidator.validate_all(
            product=invoice.product,
            customer=invoice.customer,
            quantity=invoice.quantity,
            unit=invoice.unit,
            unit_price=invoice.unit_price,
            movement_id=invoice.movement_id,
            date=invoice.date,
            total_price=invoice.total_price
        )

        self.invoices.append(invoice)
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(
                movement.user_id,
                "GENERATE_INVOICE",
                f"Invoice generated for movement {movement.movement_id}, customer={customer}"
            )

        return invoice

    # READ
    def get_all(self) -> List[Invoice]:
        return self.invoices

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        return next((inv for inv in self.invoices if inv.invoice_id == invoice_id), None)

    def get_by_movement_id(self, movement_id: str) -> Optional[Invoice]:
        movement_id = str(movement_id)
        return next((inv for inv in self.invoices if str(inv.movement_id) == movement_id), None)

    # SEARCH
    def search_by_customer(self, keyword: str) -> List[Invoice]:
        return filter_by_customer(self.invoices, keyword)

    def search_by_product(self, keyword: str) -> List[Invoice]:
        return filter_by_product(self.invoices, keyword)

    def search_by_date(self, date_str: str) -> List[Invoice]:
        InvoiceValidator.validate_date(date_str)
        return filter_by_date(self.invoices, date_str)

    def search_by_total_price(self, min_value: Optional[float] = None,
                              max_value: Optional[float] = None) -> List[Invoice]:
        return filter_by_total_range(self.invoices, min_value, max_value)


    # Търсене на фактури по обща сума.
    # Приема минимална и/или максимална стойност като текст (от потребителя).
    # Празен вход или невалидно число се игнорират и се третират като None.
    # Преобразува въведените стойности към float, ако е възможно.
    # Връща всички фактури, чиито total_price попадат в зададения диапазон.
    def search_by_total(self, min_total: Optional[str] = None,
                        max_total: Optional[str] = None) -> List[Invoice]:

        # Преобразуваме входа към числа или None
        try:
            min_val = float(min_total) if min_total not in (None, "", " ") else None
        except:
            min_val = None

        try:
            max_val = float(max_total) if max_total not in (None, "", " ") else None
        except:
            max_val = None

        return filter_by_total_range(self.invoices, min_val, max_val)

    # UPDATE
    def update_customer(self, invoice_id: str, new_customer: str) -> bool:
        InvoiceValidator.validate_invoice_exists(invoice_id, self.invoices)
        InvoiceValidator.validate_customer(new_customer)

        inv = self.get_by_id(invoice_id)
        inv.customer = new_customer
        inv.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(new_customer, "EDIT_INVOICE",
                                      f"Updated customer for invoice {invoice_id}")

        return True

    # DELETE
    def remove(self, invoice_id: str) -> bool:
        original_len = len(self.invoices)
        self.invoices = [inv for inv in self.invoices if inv.invoice_id != invoice_id]

        if len(self.invoices) < original_len:
            self.save_changes()
            if self.activity_log:
                self.activity_log.add_log("system", "DELETE_INVOICE",
                                          f"Deleted invoice {invoice_id}")
            return True

        return False

    # ADVANCED SEARCH
    def advanced_search(self, customer: Optional[str] = None, product: Optional[str] = None,
                        start_date: Optional[str] = None, end_date: Optional[str] = None,
                        min_total: Optional[float] = None,
                        max_total: Optional[float] = None) -> List[Invoice]:

        InvoiceValidator.validate_search_filters(start_date, end_date, min_total, max_total)

        return filter_advanced(
            self.invoices,
            customer=customer,
            product=product,
            start_date=start_date,
            end_date=end_date,
            min_total=min_total,
            max_total=max_total
        )

    # SAVE
    def save_changes(self) -> None:
        self.repo.save([inv.to_dict() for inv in self.invoices])
