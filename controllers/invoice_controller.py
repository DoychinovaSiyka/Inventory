from typing import List, Optional
from models.invoice import Invoice
from validators.invoice_validator import InvoiceValidator
from filters.invoice_filters import (filter_by_customer, filter_by_product, filter_by_date,
                                     filter_by_total_range, filter_by_date_range, filter_advanced)


class InvoiceController:
    """ Контролерът управлява жизнения цикъл на фактурите. """
    def __init__(self, repo, activity_log_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller
        self.invoices: List[Invoice] = []
        self._reload()


    def _reload(self):
        """ Зарежда фактурите от хранилището. """
        raw = self.repo.load() or []
        self.invoices = [Invoice.from_dict(inv) for inv in raw if isinstance(inv, dict)]

    def _save_changes(self):
        """ Записва текущото състояние в хранилището. """
        self.repo.save([inv.to_dict() for inv in self.invoices])

    def _log(self, user_id: str, action: str, message: str):
        """ Помощен метод за записване на активност. """
        if self.activity_log:
            self.activity_log.log_action(user_id, action, message)

    def add(self, invoice_data: dict, user_id: str) -> Invoice:
        InvoiceValidator.validate_all(**invoice_data)

        invoice = Invoice(**invoice_data)
        self.invoices.append(invoice)
        self._save_changes()
        self._log(user_id, "GENERATE_INVOICE", f"Ръчно генерирана фактура #{invoice.invoice_id[:8]}")
        return invoice

    def create_from_movement(self, movement, product, customer: str, user_id: str) -> Invoice:
        """Автоматично генериране при продажба - чрез запечатване на данни.
        Взема историческите данни директно от обекта Movement."""
        qty = float(movement.quantity)

        # Ползваме запечатаната цена от движението, а не текущата от каталога
        unit_price = float(movement.price)
        total_price = round(qty * unit_price, 2)

        # Вземаме запечатаното име от движението
        invoice = Invoice(product=movement.product_name, quantity=qty, unit=movement.unit,
                          unit_price=unit_price, total_price=total_price, customer=customer,
                          movement_id=movement.movement_id, date=movement.date, created=movement.date,
                          modified=movement.date, invoice_id=None)

        self.invoices.append(invoice)
        self._save_changes()
        self._log(user_id, "GENERATE_INVOICE", f"Автоматична фактура от продажба на {movement.product_name}")
        return invoice

    def get_all(self) -> List[Invoice]:
        """ Връща списък с всички фактури. """
        return self.invoices or []

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        target_id = str(invoice_id).strip()
        if not target_id:
            return None


        for inv in self.invoices:
            if inv.invoice_id == target_id:
                return inv
        return None


        for inv in self.invoices:
            if inv.invoice_id.startswith(target_id):
                return inv

        return None

    def remove(self, invoice_id: str, user_id: str) -> bool:
        inv = self.get_by_id(invoice_id)
        if not inv:
            return False

        self.invoices = [i for i in self.invoices if i.invoice_id != inv.invoice_id]
        self._save_changes()
        self._log(user_id, "DELETE_INVOICE", f"Изтрита фактура #{inv.invoice_id[:8]}")
        return True

    def search_by_customer(self, keyword: str) -> List[Invoice]:
        clean_keyword = str(keyword or "").strip()
        if not clean_keyword:
            return self.get_all()
        return filter_by_customer(self.invoices, clean_keyword) or []

    def search_by_product(self, keyword: str) -> List[Invoice]:
        """ Търсене по име на продукт (историческо). """
        clean_keyword = str(keyword or "").strip()
        if not clean_keyword:
            return self.get_all()
        return filter_by_product(self.invoices, clean_keyword) or []

    def search_by_date(self, date_str: str) -> List[Invoice]:
        InvoiceValidator.validate_date(date_str)
        return filter_by_date(self.invoices, date_str) or []

    def advanced_search(self, **kwargs) -> List[Invoice]:
        """ Търсене по множество критерии. """
        InvoiceValidator.validate_search_filters(kwargs.get("start_date"), kwargs.get("end_date"),
                                                 kwargs.get("min_total"), kwargs.get("max_total"))
        return filter_advanced(self.invoices, **kwargs) or []