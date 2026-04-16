from datetime import datetime
from models.report import Report
from storage.json_repository import JSONRepository
from filters.report_filters import (
    filter_out_invoices, filter_movements_by_product,
    group_turnover_by_day, group_top_products
)


class ReportController:
    """ Контролер за отчети. Координира данни от други контролери и филтри,
    създава Report обекти и ги записва чрез JSONRepository. Не съдържа бизнес логика. """

    def __init__(self, repo: JSONRepository, product_controller, movement_controller,
                 invoice_controller, location_controller):
        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        raw_data = self.repo.load()
        self.reports = []

        # Защита при повреден JSON
        if isinstance(raw_data, list):
            self.reports = [Report.from_dict(r) for r in raw_data if isinstance(r, dict)]

    # INTERNAL HELPERS
    @staticmethod
    def _now() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _create_report(self, report_type: str, parameters: dict, data):
        """Вътрешен помощен метод за създаване на обект Report."""
        return Report(report_type=report_type, generated_on=self._now(),
                      parameters=parameters, data=data)

    # СПРАВКА 1: Наличности
    def report_stock(self) -> Report:
        """ Генерира отчет за наличностите по продукти и складове. """
        data = []

        for p in self.product_controller.get_all():
            loc = self.location_controller.get_by_id(p.location_id)
            location_name = loc.name if loc else "Няма склад"

            data.append({"product": p.name, "quantity": round(float(p.quantity), 2),
                         "price": round(float(p.price), 2), "location": location_name})

        return self._create_report("stock", {}, data)

    # СПРАВКА 2: Движения
    def report_movements(self) -> Report:
        """ Генерира отчет за всички движения в склада. """
        data = []

        for m in self.movement_controller.get_all():
            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "Неизвестен продукт"

            loc = self.location_controller.get_by_id(m.location_id)
            location_name = loc.name if loc else "Неизвестен склад"

            movement_price = m.price if m.movement_type.name in ("IN", "OUT") else None
            data.append({"date": m.date, "type": m.movement_type.name, "movement_id": m.movement_id,
                         "quantity": m.quantity, "price": movement_price, "location_name": location_name})

        return self._create_report("movements_history", {}, data)

    # СПРАВКА 3: Обороти
    def report_turnover_by_day(self):
        """Генерира отчет за оборота по дни на база фактури."""
        invoices = filter_out_invoices(self.invoice_controller.invoices, self.movement_controller.movements)
        data = group_turnover_by_day(invoices)

        return self._create_report("turnover_by_day", {}, data)

    # СПРАВКА 4: Топ продукти
    def report_top_products(self):
        """Генерира отчет за най-продаваните продукти."""
        invoices = filter_out_invoices(self.invoice_controller.invoices, self.movement_controller.movements)
        data = group_top_products(invoices)

        return self._create_report("top_products", {}, data)

    # СПРАВКА 5: Всички фактури / продажби
    def report_sales(self) -> Report:
        """ Генерира отчет за всички издадени фактури (продажби). """
        data = []
        for inv in self.invoice_controller.invoices:
            movement = self.movement_controller.get_by_id(inv.movement_id)
            product_name = "N/A"
            if movement:
                product = self.product_controller.get_by_id(movement.product_id)
                product_name = product.name if product else "Изтрит продукт"

            client = inv.customer if inv.customer else "Неизвестен"
            total = round(float(inv.total_price), 2)
            data.append({"invoice_number": invoice_number, "date": inv.date, "client": client,
                         "product": product_name, "total_amount": total, "tax_amount": 0.00})

        return self._create_report("sales_all", {}, data)

    # СПРАВКА: Продажби по клиент
    def report_sales_by_customer(self, customer: str) -> Report:
        """ Генерира отчет за продажби, филтрирани по клиент. """
        customer = customer.lower().strip()
        search_parts = customer.split()
        data = []

        for inv in self.invoice_controller.invoices:
            client_name = inv.customer.lower() if inv.customer else ""
            if not all(part in client_name for part in search_parts):
                continue

            total = round(float(inv.total_price), 2)

            data.append({"invoice_number": inv.invoice_id, "date": inv.date, "client": inv.customer,
                         "product": inv.product, "total_amount": total})

        return self._create_report("sales_by_customer", {"customer": customer}, data)

    # СПРАВКА: Продажби по продукт
    def report_sales_by_product(self, product_name: str) -> Report:
        """ Генерира отчет за продажби, филтрирани по продукт. """
        product_name = product_name.lower()
        data = []

        for inv in self.invoice_controller.invoices:
            if product_name not in inv.product.lower():
                continue
            total = round(float(inv.total_price), 2)
            data.append({"invoice_number": inv.invoice_id, "date": inv.date, "client": inv.customer,
                         "product": inv.product, "total_amount": total})

        return self._create_report("sales_by_product", {"product": product_name}, data)

    # СПРАВКА: Продажби по дата
    def report_sales_by_date(self, date_str: str) -> Report:
        """Генерира отчет за продажби по конкретна дата (или начало на дата)."""
        data = []
        for inv in self.invoice_controller.invoices:
            if not inv.date.startswith(date_str):
                continue
            total = round(float(inv.total_price), 2)

            data.append({"invoice_number": inv.invoice_id, "date": inv.date,
                         "client": inv.customer, "product": inv.product, "total_amount": total})

        return self._create_report("sales_by_date", {"date": date_str}, data)

    # СПРАВКА: Всички доставки (IN)
    def report_deliveries_all(self) -> Report:
        """ Генерира отчет за всички доставки (IN движения). """
        data = []
        for m in self.movement_controller.movements:
            if m.movement_type.name != "IN":
                continue
            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "Неизвестен продукт"

            loc = self.location_controller.get_by_id(m.location_id)
            location_name = loc.name if loc else "Неизвестен склад"

            supplier_name = "-"
            if m.supplier_id:
                supplier = self.movement_controller.supplier_controller.get_by_id(m.supplier_id)
                supplier_name = supplier.name if supplier else "-"

            data.append({"date": m.date, "movement_id": m.movement_id, "product": product_name,
                         "quantity": m.quantity, "supplier": supplier_name, "location_name": location_name})

        return self._create_report("deliveries_all", {}, data)

    # СПРАВКА: Търсене на доставка (IN)
    def search_deliveries_all(self, keyword: str) -> Report:
        """ Генерира отчет за доставки, филтрирани по ключова дума. """
        keyword = keyword.lower()
        data = []
        for m in self.movement_controller.movements:
            if m.movement_type.name != "IN":
                continue

            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "Неизвестен продукт"
            loc = self.location_controller.get_by_id(m.location_id)
            location_name = loc.name if loc else "Неизвестен склад"

            supplier_name = "-"
            if m.supplier_id:
                supplier = self.movement_controller.supplier_controller.get_by_id(m.supplier_id)
                supplier_name = supplier.name if supplier else "-"

            if (keyword in m.movement_id.lower() or keyword in product_name.lower() or
                    keyword in supplier_name.lower() or keyword in m.date.lower()):
                data.append({"date": m.date, "movement_id": m.movement_id,
                             "product": product_name, "quantity": m.quantity, "supplier": supplier_name,
                             "location_name": location_name})

        return self._create_report("deliveries_search", {"keyword": keyword}, data)

    # ГЕНЕРИРАНЕ НА ПАКЕТ ОТ ОТЧЕТИ
    def generate_all_reports(self):
        """ Генерира пакет от всички видове отчети за инициализацията в main.py. """
        return [self.report_stock().to_dict(), self.report_turnover_by_day().to_dict(),
                self.report_top_products().to_dict()]

    # ЗАПИС В ХРАНИЛИЩЕ
    def save_reports_once(self, reports_list):
        """ Записва подаден списък с отчети (dict) еднократно в JSON файла. """
        if isinstance(reports_list, list):
            self.repo.save(reports_list)

    def save_changes(self):
        """ Записва всички заредени Report обекти обратно в JSON файла. """
        self.repo.save([r.to_dict() for r in self.reports])

    def save_report(self, report: Report):
        """ Добавя нов отчет в паметта и го записва в JSON файла. """
        self.reports.append(report)
        self.save_changes()
