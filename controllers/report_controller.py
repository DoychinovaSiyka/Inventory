from datetime import datetime
from models.report import Report
from storage.json_repository import JSONRepository


# Унифицирано преобразуване на фактура към dict
def _invoice_to_dict(inv):
    return {
        "invoice_id": inv.invoice_id,
        "date": inv.date,
        "product": inv.product,
        "quantity": round(float(inv.quantity), 2),
        "total_price": round(float(inv.total_price), 2),
        "customer": getattr(inv, "customer", None)
    }


# Създаване на Report обект
def _create_report(report_type, parameters, data):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return Report(
        report_type=report_type,
        generated_on=now,
        parameters=parameters,
        data=data
    )


class ReportController:
    def __init__(self, repo: JSONRepository, product_controller,
                 movement_controller, invoice_controller, location_controller):

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

    # Превръща ID (W1) в име (София)
    def _get_location_display(self, loc_id):
        if not loc_id:
            return "Няма информация"
        loc = self.location_controller.get_by_id(str(loc_id))
        return f"{loc.name} ({loc_id})" if loc else str(loc_id)

    # Унифициран метод за движение → dict
    def _movement_to_dict(self, m):
        loc = self.location_controller.get_by_id(m.location_id)
        product = self.product_controller.get_by_id(m.product_id)

        return {
            "movement_id": m.movement_id,
            "date": m.date,
            "type": m.movement_type.name,
            "product_id": m.product_id,
            "product_name": product.name if product else "Неизвестен продукт",
            "quantity": round(float(m.quantity), 2),
            "price": round(float(m.price), 2),
            "location_id": m.location_id,
            "location_name": loc.name if loc else None,
            "supplier_id": m.supplier_id if m.movement_type.name == "IN" else None,
            "customer": m.customer if m.movement_type.name == "OUT" else None
        }

    # Филтър – само фактури от OUT движения
    def _filter_out_invoices(self):
        out_invoices = []
        for inv in self.invoice_controller.invoices:
            movement = self.movement_controller.get_by_id(inv.movement_id)
            if movement and movement.movement_type.name == "OUT":
                out_invoices.append(inv)
        return out_invoices

    # СПРАВКИ – Наличности
    def report_stock(self):
        data = []
        for p in self.product_controller.products:
            loc_id = getattr(p, "location_id", None)
            data.append({
                "product": p.name,
                "quantity": round(float(p.quantity), 2),
                "price": round(float(p.price), 2),
                "location": self._get_location_display(loc_id)
            })
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
        return _create_report("movements_by_product", {"keyword": keyword}, data)

    # Движения по тип
    def report_movements_by_type(self, movement_type):
        movement_type = movement_type.upper()
        data = [
            self._movement_to_dict(m)
            for m in self.movement_controller.movements
            if m.movement_type.name == movement_type
        ]
        return _create_report("movements_by_type", {"type": movement_type}, data)

    # Движения по дата
    def report_movements_by_date(self, date_str):
        data = [
            self._movement_to_dict(m)
            for m in self.movement_controller.movements
            if m.date.startswith(date_str)
        ]
        return _create_report("movements_by_date", {"date": date_str}, data)

    # ПРОДАЖБИ – само OUT
    def report_sales(self):
        invoices = self._filter_out_invoices()
        data = [_invoice_to_dict(inv) for inv in invoices]
        return _create_report("sales_all", {}, data)

    def report_sales_by_customer(self, customer):
        invoices = [
            inv for inv in self._filter_out_invoices()
            if customer.lower() in inv.customer.lower()
        ]
        data = [_invoice_to_dict(inv) for inv in invoices]
        return _create_report("sales_by_customer", {"customer": customer}, data)

    def report_sales_by_product(self, product):
        invoices = [
            inv for inv in self._filter_out_invoices()
            if product.lower() in inv.product.lower()
        ]
        data = [_invoice_to_dict(inv) for inv in invoices]
        return _create_report("sales_by_product", {"product": product}, data)

    def report_sales_by_date(self, date_str):
        invoices = [
            inv for inv in self._filter_out_invoices()
            if inv.date.startswith(date_str)
        ]
        data = [_invoice_to_dict(inv) for inv in invoices]
        return _create_report("sales_by_date", {"date": date_str}, data)

    # Генерира всички основни отчети при стартиране
    def generate_all_reports(self):
        return [
            self.report_stock(),
            self.report_movements(),
            self.report_sales()
        ]
    # ПРОДАЖБИ – обработка на данни (НЕ е View логика)
    def _process_data(self, data):
        rows = []
        has_id = False
        for item in data:
            row_id = item.get('invoice_id')
            if row_id:
                has_id = True

            p_name = item.get('product', '—')
            qty = float(item.get('quantity', 0) or 0)

            raw_total = item.get('total_price', item.get('total', 0))
            total = float(raw_total or 0)

            raw_price = item.get('price')
            if raw_price is None or raw_price == 0:
                price = round(total / qty, 2) if qty > 0 else 0
            else:
                price = round(float(raw_price), 2)

            rows.append([
                row_id,
                p_name,
                qty,
                price,
                total,
                item.get('customer'),
                item.get('date')
            ])

        return rows, has_id

    # ДВИЖЕНИЯ – нормализиране на данни (НЕ е View логика)
    def _normalize_movement_row(self, item):
        loc_id = (
            item.get('location_id') or item.get('location') or
            item.get('loc') or item.get('warehouse') or item.get('warehouse_id')
        )

        location = self.location_controller.get_by_id(loc_id) if loc_id else None
        location_name = location.name if location else "Няма склад"

        return [
            item.get('date'),
            item.get('type'),
            item.get('movement_id'),
            item.get('quantity'),
            item.get('price'),
            location_name
        ]

    # Записва отчетите само ако такъв тип още не съществува
    def save_reports_once(self, reports):
        existing_types = {r.report_type for r in self.reports}
        for r in reports:
            if r.report_type not in existing_types:
                self.reports.append(r)
        self.save_changes()
