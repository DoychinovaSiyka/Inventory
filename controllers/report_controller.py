from datetime import datetime
from models.report import Report
from storage.json_repository import JSONRepository


def _invoice_to_dict(inv):
    return {
        "invoice_id": inv.invoice_id, "date": inv.date,
        "product": inv.product, "quantity": round(float(inv.quantity), 2),
        "total_price": round(float(inv.total_price), 2),
        "customer": getattr(inv, "customer", None)
    }


def _create_report(report_type, parameters, data):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return Report(report_type=report_type, generated_on=now,
                  parameters=parameters, data=data)


class ReportController:
    def __init__(self, repo: JSONRepository, product_controller, movement_controller,
                 invoice_controller, location_controller):
        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        # Зареждаме всички справки от JSON (история)
        self.reports = [Report.from_dict(r) for r in self.repo.load()]


    # Записване на всички справки
    def save_changes(self):
        self.repo.save([r.to_dict() for r in self.reports])

    # Запазване на конкретен отчет
    def save_report(self, report):
        self.reports.append(report)
        self.save_changes()

    # Създаване на нов отчет (НЕ го записва автоматично)
    # Превръща ID (W1) в име (София)
    def _get_location_display(self, loc_id):
        if not loc_id:
            return "Няма информация"
        loc = self.location_controller.get_by_id(str(loc_id))
        return f"{loc.name} ({loc_id})" if loc else str(loc_id)

    # Унифициран метод за движение - dict
    def _movement_to_dict(self, m):
        loc_id = m.location_id
        loc = self.location_controller.get_by_id(loc_id)
        loc_name = loc.name if loc else None
        product = self.product_controller.get_by_id(m.product_id)
        product_name = product.name if product else "Неизвестен продукт"

        return {
            "movement_id": m.movement_id, "date": m.date,
            "type": m.movement_type.name, "product_id": m.product_id,
            "product_name": product_name, "quantity": round(float(m.quantity), 2),
            "price": round(float(m.price), 2), "location_id": loc_id,
            "location_name": loc_name, "supplier_id": m.supplier_id
            if m.movement_type.name == "IN" else None,
            "customer": m.customer if m.movement_type.name == "OUT" else None
        }

    # Филтър - само фактури от OUT движения
    def _filter_out_invoices(self):
        out_invoices = []
        for inv in self.invoice_controller.invoices:
            movement = self.movement_controller.get_by_id(inv.movement_id)
            if movement and movement.movement_type.name == "OUT":
                out_invoices.append(inv)
        return out_invoices

    # СПРАВКИ - Справка за наличности
    def report_stock(self):
        data = []
        for p in self.product_controller.products:
            loc_id = getattr(p, "location_id", None)
            data.append({"product": p.name, "quantity": round(float(p.quantity), 2),
                         "price": round(float(p.price), 2), "location": self._get_location_display(loc_id)})
        return _create_report("stock", {}, data)

    # Всички движения
    def report_movements(self):
        data = [self._movement_to_dict(m) for m in self.movement_controller.movements]
        return _create_report("movements_all", {}, data)

    # Движения по продукт
    def report_movements_by_product(self, keyword):
        keyword = keyword.lower()
        data = []
        for m in self.movement_controller.movements:
            product = self.product_controller.get_by_id(m.product_id)
            if product and keyword in product.name.lower():
                data.append(self._movement_to_dict(m))

        return _create_report("movements_by_product",
                              {"keyword": keyword}, data)

    # Движения по тип
    def report_movements_by_type(self, movement_type):
        movement_type = movement_type.upper()
        data = [self._movement_to_dict(m) for m in self.movement_controller.movements
                if m.movement_type.name == movement_type]
        return _create_report("movements_by_type",
                              {"type": movement_type}, data)

    # Движения по дата
    def report_movements_by_date(self, date_str):
        data = [self._movement_to_dict(m) for m in self.movement_controller.movements
                if m.date.startswith(date_str)]
        return _create_report("movements_by_date",
                              {"date": date_str}, data)

    # ПРОДАЖБИ - САМО OUT
    def report_sales(self):
        invoices = self._filter_out_invoices()
        data = [_invoice_to_dict(inv) for inv in invoices]
        return _create_report("sales_all", {}, data)

    def report_sales_by_customer(self, customer):
        invoices = self._filter_out_invoices()
        invoices = [inv for inv in invoices if customer.lower() in inv.customer.lower()]
        data = [_invoice_to_dict(inv) for inv in invoices]
        return _create_report("sales_by_customer", {"customer": customer}, data)

    def report_sales_by_product(self, product):
        invoices = self._filter_out_invoices()
        invoices = [inv for inv in invoices if product.lower() in inv.product.lower()]
        data = [_invoice_to_dict(inv) for inv in invoices]
        return _create_report("sales_by_product", {"product": product}, data)

    def report_sales_by_date(self, date_str):
        invoices = self._filter_out_invoices()
        invoices = [inv for inv in invoices if inv.date.startswith(date_str)]
        data = [_invoice_to_dict(inv) for inv in invoices]
        return _create_report("sales_by_date", {"date": date_str}, data)


    #  АВТОМАТИЧНО ГЕНЕРИРАНЕ И ЗАПИСВАНЕ САМО ВЕДНЪЖ
    def generate_all_reports(self):
        """Генерира всички основни отчети при стартиране."""
        return [self.report_stock(),self.report_movements(),self.report_sales()]


    def save_reports_once(self, reports):
        """Записва отчетите само ако такъв тип още не съществува."""
        existing_types = {r.report_type for r in self.reports}
        for r in reports:
            if r.report_type not in existing_types:
                self.reports.append(r)
        self.save_changes()
