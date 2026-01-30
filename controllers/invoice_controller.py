from models.invoice import Invoice
from storage.json_repository import JSONRepository
from datetime import datetime


class InvoiceController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.invoices = self._load()

    # -----------------------------
    # Вътрешни методи
    # -----------------------------
    def _load(self):
        data = self.repo.load()
        return [Invoice.from_dict(item) for item in data]

    def _save(self):
        self.repo.save([inv.to_dict() for inv in self.invoices])

    # -----------------------------
    # Основни операции
    # -----------------------------
    def add(self, invoice: Invoice):
        """
        Добавя вече създадена фактура (използва се от MovementController).
        """
        self.invoices.append(invoice)
        self._save()
        return invoice

    def create_from_movement(self, movement, product, customer):
        """
        Генерира фактура при OUT движение.
        movement → Movement обект
        product → Product обект
        customer → име на клиента (username)
        """

        if movement.movement_type.name != "OUT":
            raise ValueError("Фактура може да се генерира само при продажба (OUT Movement).")

        invoice = Invoice(
            movement_id=movement.movement_id,
            product=product.name,
            quantity=movement.quantity,
            unit_price=movement.price,
            customer=customer
        )

        self.invoices.append(invoice)
        self._save()
        return invoice

    # -----------------------------
    # Търсене
    # -----------------------------
    def get_all(self):
        return self.invoices

    def get_by_id(self, invoice_id):
        for inv in self.invoices:
            if inv.invoice_id == invoice_id:
                return inv
        return None

    def get_by_movement_id(self, movement_id):
        for inv in self.invoices:
            if inv.movement_id == movement_id:
                return inv
        return None

    def search_by_customer(self, keyword):
        keyword = keyword.lower()
        return [inv for inv in self.invoices if keyword in inv.customer.lower()]

    def search_by_product(self, keyword):
        keyword = keyword.lower()
        return [inv for inv in self.invoices if keyword in inv.product.lower()]

    def search_by_date(self, date_str):
        """
        date_str = '2025-01-30'
        """
        return [inv for inv in self.invoices if inv.date.startswith(date_str)]

    # -----------------------------
    # Изтриване (ако е нужно)
    # -----------------------------
    def remove(self, invoice_id):
        for inv in self.invoices:
            if inv.invoice_id == invoice_id:
                self.invoices.remove(inv)
                self._save()
                return True
        return False
