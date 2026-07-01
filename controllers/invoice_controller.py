from typing import Optional, List
from models.invoice import Invoice
from validators.invoice_validator import InvoiceValidator
from controllers.abstract_controller import AbstractController


class InvoiceController(AbstractController):
    """Чист MVC контролер за фактури – без цикличност, без enterprise зависимости."""

    def __init__(self, repo):
        super().__init__(repo)
        self.invoices = self.load() or []

    def from_dict(self, data):
        return Invoice.from_dict(data)

    def to_dict(self, obj):
        return obj.to_dict()

    def _save(self):
        self.save(self.invoices)

    # -----------------------------
    # CREATE
    # -----------------------------
    def create_from_movement(self, movement, product, customer: Optional[str], user_id: str) -> Invoice:
        InvoiceValidator.validate_movement_for_invoice(movement)

        # Ако вече има фактура за това движение - връщаме я
        for inv in self.invoices:
            if inv.movement_id == movement.movement_id:
                return inv

        qty = float(movement.quantity)
        u_price = float(movement.price)
        total = round(qty * u_price, 2)
        cust_name = str(customer).strip() if customer else "Общ клиент"

        invoice = Invoice(
            product=movement.product_name,
            quantity=qty,
            unit=movement.unit,
            unit_price=u_price,
            total_price=total,
            customer=cust_name,
            movement_id=movement.movement_id,
            date=movement.date,
            invoice_id=None,
            is_active=True
        )

        self.invoices.append(invoice)
        self._save()
        return invoice

    # -----------------------------
    # GETTERS
    # -----------------------------
    def get_all(self, include_cancelled: bool = False) -> List[Invoice]:
        return self.invoices if include_cancelled else [inv for inv in self.invoices if inv.is_active]

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        tid = str(invoice_id or "").strip().lower()
        if not tid:
            return None

        for inv in self.invoices:
            if inv.invoice_id[:8].lower() == tid:
                return inv
        return None

    def search(self, query: str) -> List[Invoice]:
        q = str(query or "").strip().lower()
        return [inv for inv in self.invoices if inv.invoice_id[:8].lower() == q]

    # -----------------------------
    # REMOVE (само анулира фактура)
    # -----------------------------
    def remove(self, invoice_id: str) -> bool:
        inv = self.get_by_id(invoice_id)
        if not inv:
            return False

        if not inv.is_active:
            return False

        inv.cancel()
        self._save()
        return True
