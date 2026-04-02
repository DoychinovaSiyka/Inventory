from datetime import datetime
from models.report import Report
from storage.json_repository import JSONRepository

class ReportController:
    def __init__(self, repo: JSONRepository, product_controller, movement_controller,
                 invoice_controller, location_controller):
        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.reports = [Report.from_dict(r) for r in self.repo.load()]

    def _generate_id(self):
        if not self.reports:
            return 1
        return max(r.report_id for r in self.reports) + 1

    def save_changes(self):
        self.repo.save([r.to_dict() for r in self.reports])

    def _create_report(self, report_type, parameters, data):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report = Report(
            report_id=self._generate_id(),
            report_type=report_type,
            generated_on=now,
            parameters=parameters,
            data=data
        )
        self.reports.append(report)
        self.save_changes()
        return report

    # Помощен метод: превръща ID (W1) в име (София)
    def _get_location_display(self, loc_id):
        if not loc_id:
            return "Няма информация"
        loc = self.location_controller.get_by_id(str(loc_id))
        return f"{loc.name} ({loc_id})" if loc else str(loc_id)

    # Справка за наличности
    def report_stock(self):
        products = self.product_controller.products
        data = []
        for p in products:
            loc_id = getattr(p, "location_id", None)
            data.append({
                "product": p.name,
                "quantity": round(float(p.quantity), 2),
                "price": round(float(p.price), 2),
                "location": self._get_location_display(loc_id)
            })
        return self._create_report("stock", {}, data)

    # Всички движения
    def report_movements(self):
        movements = self.movement_controller.movements
        data = []
        for m in movements:
            data.append({
                "date": m.date,
                "type": m.movement_type.name,
                "product_id": m.product_id,
                "quantity": round(float(m.quantity), 2),
                "price": round(float(m.price), 2),
                "location": self._get_location_display(m.location_id),
                "supplier_id": m.supplier_id if m.movement_type.name == "IN" else None,
                "customer": m.customer if m.movement_type.name == "OUT" else None
            })
        return self._create_report("movements_all", {}, data)

    # Движения по продукт
    def report_movements_by_product(self, keyword):
        keyword = keyword.lower()
        data = []
        for m in self.movement_controller.movements:
            product = self.product_controller.get_by_id(m.product_id)
            if not product:
                continue
            if keyword in product.name.lower():
                data.append({
                    "date": m.date,
                    "type": m.movement_type.name,
                    "quantity": round(float(m.quantity), 2),
                    "price": round(float(m.price), 2),
                    "location": self._get_location_display(m.location_id),
                    "supplier_id": m.supplier_id if m.movement_type.name == "IN" else None,
                    "customer": m.customer if m.movement_type.name == "OUT" else None
                })
        return self._create_report("movements_by_product", {"keyword": keyword}, data)

    # Движения по тип
    def report_movements_by_type(self, movement_type):
        movement_type = movement_type.upper()
        data = []
        for m in self.movement_controller.movements:
            if m.movement_type.name == movement_type:
                data.append({
                    "date": m.date,
                    "product_id": m.product_id,
                    "quantity": round(float(m.quantity), 2),
                    "location": self._get_location_display(m.location_id),
                    "supplier_id": m.supplier_id if m.movement_type.name == "IN" else None,
                    "customer": m.customer if m.movement_type.name == "OUT" else None
                })
        return self._create_report("movements_by_type", {"type": movement_type}, data)

    # Движения по дата
    def report_movements_by_date(self, date_str):
        data = []
        for m in self.movement_controller.movements:
            if m.date.startswith(date_str):
                data.append({
                    "date": m.date,
                    "type": m.movement_type.name,
                    "quantity": round(float(m.quantity), 2),
                    "location": self._get_location_display(m.location_id),
                    "supplier_id": m.supplier_id if m.movement_type.name == "IN" else None,
                    "customer": m.customer if m.movement_type.name == "OUT" else None
                })
        return self._create_report("movements_by_date", {"date": date_str}, data)

    # Продажби
    def report_sales(self):
        invoices = self.invoice_controller.invoices
        data = [{
            "date": inv.date,
            "product": inv.product,
            "quantity": round(float(inv.quantity), 2),
            "total_price": round(float(inv.total_price), 2),
            "customer": inv.customer
        } for inv in invoices]
        return self._create_report("sales_all", {}, data)

    def report_sales_by_customer(self, customer):
        invoices = self.invoice_controller.search_by_customer(customer)
        data = [{
            "date": inv.date,
            "product": inv.product,
            "quantity": round(float(inv.quantity), 2),
            "total_price": round(float(inv.total_price), 2)
        } for inv in invoices]
        return self._create_report("sales_by_customer", {"customer": customer}, data)

    def report_sales_by_product(self, product):
        invoices = self.invoice_controller.search_by_product(product)
        data = [{
            "date": inv.date,
            "customer": inv.customer,
            "quantity": round(float(inv.quantity), 2),
            "total_price": round(float(inv.total_price), 2)
        } for inv in invoices]
        return self._create_report("sales_by_product", {"product": product}, data)

    def report_sales_by_date(self, date_str):
        invoices = self.invoice_controller.search_by_date(date_str)
        data = [{
            "product": inv.product,
            "quantity": round(float(inv.quantity), 2),
            "total_price": round(float(inv.total_price), 2),
            "customer": inv.customer
        } for inv in invoices]
        return self._create_report("sales_by_date", {"date": date_str}, data)
