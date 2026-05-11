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

    def add(self, invoice_data: dict, user_id: str) -> Invoice:
        """ Ръчно добавяне на фактура с пълна валидация. """
        InvoiceValidator.validate_all(**invoice_data)

        invoice = Invoice(**invoice_data)
        self.invoices.append(invoice)
        self._save_changes()

        return invoice

    def create_from_movement(self, movement, product, customer: Optional[str], user_id: str) -> Invoice:
        """Автоматично генерира фактура при продажба. Метод за синхрон между Склад и Счетоводство."""
        # Проверка за съществуваща фактура към това движение
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
        """ Хронологията на фактурите."""
        if include_cancelled:
            return self.invoices
        return [inv for inv in self.invoices if inv.is_active]

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """ Търси фактура по пълно или частично ID. """
        tid = str(invoice_id or "").strip()
        if not tid:
            return None

        for inv in self.invoices:
            if inv.invoice_id == tid:
                return inv

        if len(tid) >= 4:
            for inv in self.invoices:
                if inv.invoice_id.startswith(tid):
                    return inv
            return None

        return None

    def remove(self, invoice_id: str, user_id: str) -> bool:
        """ АНУЛИРА фактура"""
        inv = self.get_by_id(invoice_id)
        if not inv or not inv.is_active:
            # Ако не съществува или вече е анулирана
            return False


        inv.cancel()

        self._save_changes()
        return True



    def search_by_customer(self, keyword: str) -> List[Invoice]:
        """ Филтрира фактури по име на контрагент. """
        return invoice_filters.filter_by_customer(self.invoices, keyword)

    def search_by_product(self, keyword: str) -> List[Invoice]:
        """ Филтрира фактури по име на артикул. """
        return invoice_filters.filter_by_product(self.invoices, keyword)

    def search_by_date(self, date_str: str) -> List[Invoice]:
        """ Връща всички фактури за конкретен ден. """
        InvoiceValidator.validate_date(date_str)
        return invoice_filters.filter_by_date(self.invoices, date_str)

    def advanced_search(self, **kwargs) -> List[Invoice]:
        InvoiceValidator.validate_search_filters(kwargs.get("start_date"), kwargs.get("end_date"), kwargs.get("min_total"),
                                                 kwargs.get("max_total"))
        return invoice_filters.filter_advanced(self.invoices, **kwargs)