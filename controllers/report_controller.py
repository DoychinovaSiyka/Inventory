from models.movement import MovementType
from models.report import Report
from datetime import datetime


class ReportResult:
    def __init__(self, data):
        self.data = data


class ReportController:
    """Контролер за справки. Не пази състояние и не променя модели.
    Събира данни от другите контролери и ги връща към View."""

    def __init__(self, repo, product_controller, movement_controller,
                 invoice_controller, location_controller, inventory_controller):

        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller

    # вътрешен метод – автоматично записване на отчет
    def _save_report(self, report_type, parameters, data):
        report = Report(
            report_type=report_type,
            generated_on=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            parameters=parameters,
            data=data
        )

        all_reports = self.repo.get_all() or []
        all_reports.append(report.to_dict())
        self.repo.save(all_reports)

    # Справка - всички движения
    def report_movements(self):
        data = []

        for m in self.movement_controller.movements:
            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "Неизвестен продукт"

            location = self.location_controller.get_by_id(m.location_id)
            location_name = location.name if location else "N/A"

            data.append({"movement_id": m.movement_id,
                         "product_name": product_name, "type": m.movement_type.name,
                         "quantity": m.quantity, "unit": m.unit,
                         "price": m.price, "location_name": location_name,
                         "date": m.date})

        self._save_report("movements", {}, data)
        return ReportResult(data)

    # Справка - всички продажби
    def report_sales(self):
        invoices = self.invoice_controller.get_all() or []
        data = []

        for inv in invoices:
            data.append({"invoice_number": inv.invoice_id, "date": inv.date,
                         "client": inv.customer, "product": inv.product,
                         "total_price": inv.total_price})

        self._save_report("sales", {}, data)
        return ReportResult(data)

    # Справка - продажби по клиент
    def report_sales_by_customer(self, customer):
        customer = customer.lower()
        invoices = self.invoice_controller.get_all() or []
        data = []

        for inv in invoices:
            if inv.customer and customer in inv.customer.lower():
                data.append({"invoice_number": inv.invoice_id,
                             "date": inv.date, "client": inv.customer,
                             "product": inv.product,
                             "total_price": inv.total_price})

        self._save_report("sales_by_customer", {"customer": customer}, data)
        return ReportResult(data)

    # Справка - продажби по продукт
    def report_sales_by_product(self, product):
        product = product.lower()
        invoices = self.invoice_controller.get_all() or []
        data = []

        for inv in invoices:
            if inv.product and product in inv.product.lower():
                data.append({"invoice_number": inv.invoice_id,
                             "date": inv.date, "client": inv.customer,
                             "product": inv.product,
                             "total_price": inv.total_price})

        self._save_report("sales_by_product", {"product": product}, data)
        return ReportResult(data)

    # Справка - продажби по дата
    def report_sales_by_date(self, date):
        invoices = self.invoice_controller.get_all() or []
        data = []
        for inv in invoices:
            if inv.date and date in inv.date:
                data.append({"invoice_number": inv.invoice_id,
                             "date": inv.date, "client": inv.customer,
                             "product": inv.product,
                             "total_price": inv.total_price})

        self._save_report("sales_by_date", {"date": date}, data)
        return ReportResult(data)

    # Справка - всички доставки (IN)
    def report_deliveries_all(self, keyword=None):
        data = []

        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.IN:
                continue

            # Филтър за реални доставки
            if m.supplier_id is None:
                continue
            if m.user_id == "system":
                continue
            if m.description and ("начално" in m.description.lower() or "корекция" in m.description.lower()):
                continue

            product = self.product_controller.get_by_id(m.product_id)
            if not product:
                continue

            product_name = product.name

            location = self.location_controller.get_by_id(m.location_id)
            location_name = location.name if location else "N/A"

            supplier_name = "N/A"
            if self.movement_controller.supplier_controller:
                supplier = self.movement_controller.supplier_controller.get_by_id(m.supplier_id)
                supplier_name = supplier.name if supplier else "N/A"

            row = {"date": m.date, "movement_id": m.movement_id,
                   "product": product_name, "quantity": m.quantity,
                   "unit": m.unit, "supplier": supplier_name,
                   "location_name": location_name}

            if keyword:
                k = keyword.lower()
                if k not in product_name.lower() \
                   and k not in supplier_name.lower() \
                   and k not in location_name.lower():
                    continue

            data.append(row)

        self._save_report("deliveries_all", {"keyword": keyword}, data)
        return ReportResult(data)

    # Справка - оборот по дни
    def report_turnover_by_day(self):
        invoices = self.invoice_controller.get_all() or []
        daily = {}

        for inv in invoices:
            day = inv.date[:10] if inv.date else "N/A"
            if day not in daily:
                daily[day] = {"count": 0, "total": 0.0}

            daily[day]["count"] += 1
            daily[day]["total"] += inv.total_price

        data = [{"date": d, "count": v["count"], "total": v["total"]} for d, v in daily.items()]

        self._save_report("turnover_by_day", {}, data)
        return ReportResult(data)

    # Справка - най-продавани продукти
    def report_top_products(self):
        stats = {}

        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.OUT:
                continue

            product = self.product_controller.get_by_id(m.product_id)
            if not product:
                continue

            name = product.name
            if name not in stats:
                stats[name] = {"quantity": 0, "total": 0.0, "unit": product.unit}

            stats[name]["quantity"] += m.quantity
            stats[name]["total"] += m.quantity * m.price

        data = [{"product": name, "quantity": info["quantity"],
                 "total": info["total"], "unit": info["unit"]}
                for name, info in stats.items()]

        data.sort(key=lambda x: x["quantity"], reverse=True)

        self._save_report("top_products", {}, data)
        return ReportResult(data)

    # Справка - обобщена наличност
    def report_inventory_summary(self):
        if not self.inventory_controller:
            self._save_report("inventory_summary", {}, [])
            return ReportResult([])

        inv_data = self.inventory_controller.data or {}
        products_data = inv_data.get("products", {})
        data = []

        for product in self.product_controller.get_all():
            pid, unit = product.product_id, product.unit

            current_stock = self.inventory_controller.get_total_stock(pid) if self.inventory_controller else 0.0

            sold = sum(m.quantity for m in self.movement_controller.movements
                       if m.product_id == pid and
                       m.movement_type == MovementType.OUT)

            locations = products_data.get(pid, {}).get("locations", {})
            top3 = sorted(locations.items(),
                          key=lambda x: x[1], reverse=True)[:3]
            top3_str = ", ".join([f"{loc}:{qty}" for loc, qty in top3]) \
                if top3 else "-"

            data.append({"product": product.name,
                         "available": f"{current_stock} {unit}",
                         "sold": f"{sold} {unit}" if sold > 0 else "-",
                         "top_locations": top3_str})

        self._save_report("inventory_summary", {}, data)
        return ReportResult(data)

    # Справка - жизнен цикъл на продукт
    def product_lifecycle(self, name):
        name = name.lower()

        # Търся продукта по по-човешки начин, без генератори
        product = None
        for p in self.product_controller.get_all():
            if p.name and name in p.name.lower():
                product = p
                break

        if not product:
            self._save_report("product_lifecycle", {"name": name}, [])
            return None

        pid, unit = product.product_id, product.unit
        current_stock = self.inventory_controller.get_total_stock(pid) if self.inventory_controller else 0.0

        total_in = total_out = 0.0

        for m in self.movement_controller.movements:
            if m.product_id != pid:
                continue

            # Реални доставки
            if m.movement_type == MovementType.IN:
                if m.supplier_id and m.user_id != "system" and "начално" not in m.description.lower():
                    total_in += m.quantity

            # Реални продажби
            elif m.movement_type == MovementType.OUT:
                total_out += m.quantity

        initial_stock = current_stock + total_out - total_in

        data = {"product": product.name, "unit": unit,
                "initial_stock": initial_stock, "total_in": total_in,
                "total_out": total_out, "expected_stock": current_stock,
                "current_stock": current_stock,
                "revenue": total_out * product.price}

        self._save_report("product_lifecycle", {"name": name}, data)
        return data
