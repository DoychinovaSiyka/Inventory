from typing import List, Optional
from models.invoice import Invoice
from validators.invoice_validator import InvoiceValidator
from filters import invoice_filters


class InvoiceController:
    """Управлява жизнения цикъл на фактурите."""
    def __init__(self, repo):
        self.repo = repo
        self.invoices: List[Invoice] = []
        self._reload()

    def _reload(self) -> None:
        """ Зарежда всички фактури от базата и ги превръща в обекти. """
        raw = self.repo.load() or []
        self.invoices = [Invoice.from_dict(inv) for inv in raw if isinstance(inv, dict)]

    def _save_changes(self) -> None:
        """ Записва списъка с фактури обратно в базата. """
        self.repo.save([inv.to_dict() for inv in self.invoices])



    def create_from_movement(self, movement, product, customer: Optional[str], user_id: str) -> Invoice:
        """Автоматично генерира фактура при продажба."""
        for inv in self.invoices:
            if inv.movement_id == movement.movement_id:
                return inv

        qty = float(movement.quantity)
        u_price = float(movement.price)
        total = round(qty * u_price, 2)
        cust_name = str(customer).strip() if customer else "Общ клиент"

        invoice = Invoice(product=movement.product_name, quantity=qty, unit=movement.unit,
                          unit_price=u_price, total_price=total, customer=cust_name,
                          movement_id=movement.movement_id, date=movement.date,
                          invoice_id=None, is_active=True)

        self.invoices.append(invoice)
        self._save_changes()
        return invoice

    def get_all(self, include_cancelled=True) -> List[Invoice]:
        if include_cancelled:
            return self.invoices
        return [inv for inv in self.invoices if inv.is_active]

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """Търси фактура само по началото на ID-то."""
        tid = str(invoice_id or "").strip()
        if not tid:
            return None

        for inv in self.invoices:
            if inv.invoice_id.startswith(tid):
                return inv

        return None

    def remove(self, invoice_id: str, user_id: str) -> bool:
        """ АНУЛИРА фактура"""
        inv = self.get_by_id(invoice_id)
        if not inv or not inv.is_active:
            return False


        inv.cancel()

        self._save_changes()
        return True




