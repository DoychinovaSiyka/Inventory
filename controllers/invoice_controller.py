from typing import Optional, List
from datetime import datetime
from models.invoice import Invoice
from storage.json_repository import JSONRepository


class InvoiceController:
    def __init__(self, repo: JSONRepository, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller
        raw = self.repo.load()
        self.invoices: List[Invoice] = []
        # Зареждам фактурите от JSON Ако някоя няма UUID - генерирам нов
        for inv in raw:
            if not inv.get("invoice_id"):
                # нов UUID се генерира от самия модел Invoice
                invoice = Invoice.from_dict(inv)
            else:
                invoice = Invoice.from_dict(inv)
            self.invoices.append(invoice)
        self.save_changes()

    # CREATE
    def add(self, invoice: Invoice) -> Invoice:
        # UUID се генерира в конструктора на Invoice
        self.invoices.append(invoice)
        self.save_changes()
        if self.activity_log:
            self.activity_log.add_log(invoice.customer, "GENERATE_INVOICE",
                                      f"Invoice created for movement {invoice.movement_id}")
        return invoice


    def create_from_movement(self, movement, product, customer: str) -> Invoice:
        if movement.movement_type.name != "OUT":
            raise ValueError("Фактура може да се генерира само при OUT движение.")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        qty = float(movement.quantity)
        unit_price = round(float(movement.price), 2)
        total_price = round(qty * unit_price, 2)
        # UUID се генерира автоматично от Invoice()
        invoice = Invoice(movement_id=movement.movement_id, product=product.name, quantity=qty, unit=movement.unit,
                          unit_price=unit_price, total_price=total_price, customer=customer, date=now,
                          created=now, modified=now)
        self.invoices.append(invoice)
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(movement.user_id, "GENERATE_INVOICE",
                                      f"Invoice generated for movement {movement.movement_id}, "f"customer={customer}")
        return invoice

    # READ
    def get_all(self) -> List[Invoice]:
        return self.invoices

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        # UUID е string → сравняваме като string
        return next((inv for inv in self.invoices if inv.invoice_id == invoice_id), None)

    def get_by_movement_id(self, movement_id: str) -> Optional[Invoice]:
        # UUID е string → сравняваме като string
        movement_id = str(movement_id)
        return next((inv for inv in self.invoices if str(inv.movement_id) == movement_id), None)

    # SEARCH
    def search_by_customer(self, keyword: str) -> List[Invoice]:
        keyword = keyword.lower()
        return [inv for inv in self.invoices if keyword in inv.customer.lower()]

    def search_by_product(self, keyword: str) -> List[Invoice]:
        keyword = keyword.lower()
        return [inv for inv in self.invoices if keyword in inv.product.lower()]

    def search_by_date(self, date_str: str) -> List[Invoice]:
        return [inv for inv in self.invoices if inv.date.startswith(date_str)]

    def search_by_total_price(self, min_value: Optional[float] = None,
                              max_value: Optional[float] = None) -> List[Invoice]:
        results = self.invoices
        if min_value is not None:
            results = [inv for inv in results if inv.total_price >= min_value]
        if max_value is not None:
            results = [inv for inv in results if inv.total_price <= max_value]
        return results

    # UPDATE
    def update_customer(self, invoice_id: str, new_customer: str) -> bool:
        inv = self.get_by_id(invoice_id)
        if not inv:
            raise ValueError("Фактурата не е намерена.")

        inv.customer = new_customer
        inv.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.save_changes()

        if self.activity_log:
            self.activity_log.add_log(new_customer, "EDIT_INVOICE", f"Updated customer for invoice {invoice_id}")
        return True

    # DELETE
    def remove(self, invoice_id: str) -> bool:
        original_len = len(self.invoices)
        self.invoices = [inv for inv in self.invoices if inv.invoice_id != invoice_id]

        if len(self.invoices) < original_len:
            self.save_changes()
            if self.activity_log:
                self.activity_log.add_log("system", "DELETE_INVOICE", f"Deleted invoice {invoice_id}")
            return True
        return False

    # ADVANCED SEARCH
    def advanced_search(self, customer: Optional[str] = None, product: Optional[str] = None,
                        start_date: Optional[str] = None, end_date: Optional[str] = None,
                        min_total: Optional[float] = None,
                        max_total: Optional[float] = None) -> List[Invoice]:
        results = self.invoices
        # customer
        if customer:
            kw = customer.lower()
            results = [inv for inv in results if kw in inv.customer.lower()]
        # product
        if product:
            kw = product.lower()
            results = [inv for inv in results if kw in inv.product.lower()]

        # date parsing helper
        def parse_date(d):
            try:
                return datetime.strptime(d, "%Y-%m-%d")
            except:
                return None

        # parse start/end dates safely
        start = parse_date(start_date) if start_date else None
        end = parse_date(end_date) if end_date else None
        # date filtering
        if start:
            results = [inv for inv in results if parse_date(inv.date[:10])
                       and parse_date(inv.date[:10]) >= start]
        if end:
            results = [inv for inv in results if parse_date(inv.date[:10]) and parse_date(inv.date[:10]) <= end]

        # total price filtering — FIXED (convert to float safely)
        if min_total is not None:
            try:
                min_total = float(min_total)
                results = [inv for inv in results if inv.total_price >= min_total]
            except:
                pass  # игнорира невалидни стойности
        if max_total is not None:
            try:
                max_total = float(max_total)
                results = [inv for inv in results if inv.total_price <= max_total]
            except:
                pass  # игнорира невалидни стойности
        return results

    # SAVE
    def save_changes(self) -> None:
        self.repo.save([inv.to_dict() for inv in self.invoices])
