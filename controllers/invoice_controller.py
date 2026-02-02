from models.invoice import Invoice
from storage.json_repository import JSONRepository
from datetime import datetime


class InvoiceController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.invoices = [Invoice.from_dict(i) for i in self.repo.load()]

    # ---------------------------------------------------------
    # ID GENERATOR
    # ---------------------------------------------------------
    def _generate_id(self):
        if not self.invoices:
            return 1
        return max(inv.invoice_id for inv in self.invoices) + 1

    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    def add(self, invoice: Invoice):
        """Добавя вече създадена фактура (използва се от MovementController)."""
        self.invoices.append(invoice)
        self._save()
        return invoice

    def create_from_movement(self, movement, product, customer):
        """Генерира фактура при OUT движение."""

        if movement.movement_type.name != "OUT":
            raise ValueError("Фактура може да се генерира само при OUT движение.")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        invoice = Invoice(
            invoice_id=self._generate_id(),
            movement_id=movement.movement_id,
            product=product.name,
            quantity=movement.quantity,
            unit_price=movement.price,
            total_price=movement.quantity * movement.price,
            customer=customer,
            date=now,
            created=now,
            modified=now
        )

        self.invoices.append(invoice)
        self._save()
        return invoice

    # ---------------------------------------------------------
    # READ
    # ---------------------------------------------------------
    def get_all(self):
        return self.invoices

    def get_by_id(self, invoice_id):
        return next((inv for inv in self.invoices if inv.invoice_id == invoice_id), None)

    def get_by_movement_id(self, movement_id):
        return next((inv for inv in self.invoices if inv.movement_id == movement_id), None)

    # ---------------------------------------------------------
    # SEARCH
    # ---------------------------------------------------------
    def search_by_customer(self, keyword):
        keyword = keyword.lower()
        return [inv for inv in self.invoices if keyword in inv.customer.lower()]

    def search_by_product(self, keyword):
        keyword = keyword.lower()
        return [inv for inv in self.invoices if keyword in inv.product.lower()]

    def search_by_date(self, date_str):
        """date_str = '2025-01-30'"""
        return [inv for inv in self.invoices if inv.date.startswith(date_str)]

    def search_by_total_price(self, min_value=None, max_value=None):
        results = self.invoices
        if min_value is not None:
            results = [inv for inv in results if inv.total_price >= min_value]
        if max_value is not None:
            results = [inv for inv in results if inv.total_price <= max_value]
        return results

    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update_customer(self, invoice_id, new_customer):
        inv = self.get_by_id(invoice_id)
        if not inv:
            raise ValueError("Фактурата не е намерена.")

        inv.customer = new_customer
        inv.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._save()
        return True

    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------
    def remove(self, invoice_id):
        original_len = len(self.invoices)
        self.invoices = [inv for inv in self.invoices if inv.invoice_id != invoice_id]

        if len(self.invoices) < original_len:
            self._save()
            return True
        return False

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------
    def _save(self):
        self.repo.save([inv.to_dict() for inv in self.invoices])
