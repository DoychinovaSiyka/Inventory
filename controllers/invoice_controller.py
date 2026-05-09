from typing import List, Optional
from models.invoice import Invoice
from validators.invoice_validator import InvoiceValidator
from filters import invoice_filters


class InvoiceController:
    """ Контролерът управлява жизнения цикъл на фактурите. """
    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo
        self.invoices: List[Invoice] = []
        self._reload()


    def _reload(self):
        """ Зарежда всички фактури от базата и ги превръща в обекти. """
        raw = self.repo.load() or []
        self.invoices = [Invoice.from_dict(inv) for inv in raw if isinstance(inv, dict)]

    def _save_changes(self):
        """ Записва списъка с фактури обратно в базата. """
        self.repo.save([inv.to_dict() for inv in self.invoices])

    def add(self, invoice_data: dict, user_id: str) -> Invoice:
        InvoiceValidator.validate_all(**invoice_data)
        invoice = Invoice(**invoice_data)
        self.invoices.append(invoice)
        self._save_changes()
        return invoice

    def create_from_movement(self, movement, product, customer: str, user_id: str) -> Invoice:
        """ Автоматично прави фактура, когато се случи продажба в склада. """
        qty = float(movement.quantity)
        u_price = float(movement.price)
        total = round(qty * u_price, 2)


        cust_name = str(customer).strip() if customer else "Общ клиент"

        invoice = Invoice(product=movement.product_name, quantity=qty, unit=movement.unit,
                          unit_price=u_price, total_price=total, customer=cust_name,
                          movement_id=movement.movement_id, date=movement.date, invoice_id=None)

        self.invoices.append(invoice)
        self._save_changes()
        return invoice

    def get_all(self) -> List[Invoice]:
        """ Връща целия списък с фактури. """
        return self.invoices

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """ Търси конкретна фактура по нейното ID. """

        tid = str(invoice_id or "").strip()
        if not tid:
            return None

        for inv in self.invoices:
            if inv.invoice_id == tid:
                return inv

        for inv in self.invoices:
            if inv.invoice_id.startswith(tid):
                return inv

        return None

    def remove(self, invoice_id: str, user_id: str) -> bool:
        """ Изтрива фактура по ID. """
        inv = self.get_by_id(invoice_id)
        if not inv: return False
        self.invoices = [i for i in self.invoices if i.invoice_id != inv.invoice_id]
        self._save_changes()
        return True


    def search_by_customer(self, keyword: str) -> List[Invoice]:
        """ Справка по име на клиент. """
        return invoice_filters.filter_by_customer(self.invoices, keyword)

    def search_by_product(self, keyword: str) -> List[Invoice]:
        """ Справка по име на продукт. """
        return invoice_filters.filter_by_product(self.invoices, keyword)

    def search_by_date(self, date_str: str) -> List[Invoice]:
        """ Справка за фактури от конкретна дата. """
        InvoiceValidator.validate_date(date_str)
        return invoice_filters.filter_by_date(self.invoices, date_str)

    def advanced_search(self, **kwargs) -> List[Invoice]:
        """ Справка по много критерии едновременно (дати + цени + имена). """
        InvoiceValidator.validate_search_filters(kwargs.get("start_date"), kwargs.get("end_date"),
                                                 kwargs.get("min_total"), kwargs.get("max_total"))
        return invoice_filters.filter_advanced(self.invoices, **kwargs)