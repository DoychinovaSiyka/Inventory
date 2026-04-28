from models.movement import MovementType
from models.report import Report


class ReportResult:
    """ Помощен клас за връщане на резултат от справка към View-то. """
    def __init__(self, summary, data):
        self.summary = summary
        self.data = data


class ReportController:
    """Контролер за справки. Не пази състояние и не променя модели."""

    def __init__(self, repo, product_controller, movement_controller,
                 invoice_controller, location_controller, inventory_controller):
        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller

    # вътрешен метод – автоматично записване на отчет чрез модела Report
    def _save_report(self, report_type, parameters, summary, data):
        report = Report(report_type=report_type, parameters=parameters,
                        data={"summary": summary, "data": data})

        all_reports_raw = self.repo.load() or []
        all_reports_raw.append(report.to_dict())
        self.repo.save(all_reports_raw)

    # вътрешен метод за изчисляване на основни статистики
    def _build_summary(self, data):
        total_qty = 0.0
        total_value = 0.0

        for item in data:
            qty = item.get("quantity", 0)
            price = item.get("price", 0)
            total_qty += qty
            total_value += (qty * price)

        return {"total_records": len(data), "total_quantity": round(total_qty, 2), "total_value": round(total_value, 2)}

    # Справка - всички движения
    def report_movements(self):
        data = []
        for m in self.movement_controller.movements:
            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "Неизвестен продукт"

            location = self.location_controller.get_by_id(m.location_id)
            location_name = location.name if location else "-"

            data.append({"movement_id": m.movement_id, "product": product_name,
                         "type": m.movement_type.name, "quantity": m.quantity, "unit": m.unit,
                         "price": m.price, "location": location_name, "date": m.date[:10]})

        summary = self._build_summary(data)
        self._save_report("movements", {}, summary, data)
        return ReportResult(summary, data)

    # Справка - всички продажби (ВЕЧЕ Е ИЗВЪН report_movements)
    def report_sales(self):
        invoices = self.invoice_controller.get_all() or []
        data = []
        for inv in invoices:
            data.append({"invoice_number": inv.invoice_id, "date": inv.date[:10],
                         "client": inv.customer or "-", "product": inv.product, "quantity": inv.quantity,
                         "unit_price": inv.unit_price, "total_price": inv.total_price})

        summary = {"total_sales": len(data), "total_revenue": round(sum(i["total_price"] for i in data), 2)}

        self._save_report("sales", {}, summary, data)
        return ReportResult(summary, data)

    # Справка - продажби по клиент
    def report_sales_by_customer(self, customer):
        customer_clean = customer.lower()
        invoices = self.invoice_controller.get_all() or []
        data = []
        for inv in invoices:
            if inv.customer and customer_clean in inv.customer.lower():
                data.append({"invoice_number": inv.invoice_id, "date": inv.date[:10],
                             "client": inv.customer, "product": inv.product, "quantity": inv.quantity,
                             "total_price": inv.total_price})

        summary = {"customer": customer, "total_sales": len(data),
                   "total_revenue": round(sum(i["total_price"] for i in data), 2)}

        self._save_report("sales_by_customer", {"customer": customer}, summary, data)
        return ReportResult(summary, data)

    # Справка - продажби по продукт
    def report_sales_by_product(self, product):
        product_clean = product.lower()
        invoices = self.invoice_controller.get_all() or []
        data = []
        for inv in invoices:
            if inv.product and product_clean in inv.product.lower():
                data.append({"invoice_number": inv.invoice_id, "date": inv.date[:10],
                             "client": inv.customer or "-", "product": inv.product, "quantity": inv.quantity,
                             "total_price": inv.total_price})

        summary = {"product": product, "total_sales": len(data),
                   "total_revenue": round(sum(i["total_price"] for i in data), 2)}

        self._save_report("sales_by_product", {"product": product}, summary, data)
        return ReportResult(summary, data)

    # Справка - продажби по дата
    def report_sales_by_date(self, date_obj):
        invoices = self.invoice_controller.get_all() or []
        data = []
        date_str = date_obj.strftime("%Y-%m-%d")
        for inv in invoices:
            if inv.date and inv.date.startswith(date_str):
                data.append({"invoice_number": inv.invoice_id, "date": inv.date[:10],
                             "client": inv.customer or "-", "product": inv.product, "quantity": inv.quantity,
                             "total_price": inv.total_price})

        summary = {"date": date_str, "total_sales": len(data),
                   "total_revenue": round(sum(i["total_price"] for i in data), 2)}

        self._save_report("sales_by_date", {"date": date_str}, summary, data)
        return ReportResult(summary, data)

    # Справка - всички доставки (IN)
    def report_deliveries_all(self, keyword=None):
        data = []
        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.IN:
                continue
            if m.supplier_id is None or m.user_id == "system":
                continue
            if m.description and ("начално" in m.description.lower() or "корекция" in m.description.lower()):
                continue

            product = self.product_controller.get_by_id(m.product_id)
            if not product:
                continue

            location = self.location_controller.get_by_id(m.location_id)
            location_name = location.name if location else "-"

            supplier_name = "-"
            if self.movement_controller.supplier_controller:
                supplier = self.movement_controller.supplier_controller.get_by_id(m.supplier_id)
                supplier_name = supplier.name if supplier else "-"

            row = {"movement_id": m.movement_id, "date": m.date[:10], "product": product.name,
                   "quantity": m.quantity, "unit": m.unit, "supplier": supplier_name, "location": location_name}

            if keyword:
                k = keyword.lower()
                if k not in product.name.lower() and k not in supplier_name.lower() and k not in location_name.lower():
                    continue
            data.append(row)

        summary = self._build_summary(data)
        self._save_report("deliveries_all", {"keyword": keyword}, summary, data)
        return ReportResult(summary, data)

    # Справка - оборот по дни
    def report_turnover_by_day(self):
        invoices = self.invoice_controller.get_all() or []
        daily = {}
        for inv in invoices:
            day = inv.date[:10] if inv.date else "-"
            if day not in daily:
                daily[day] = {"count": 0, "total": 0.0}
            daily[day]["count"] += 1
            daily[day]["total"] += inv.total_price

        data = [{"date": d, "count": v["count"], "total": v["total"]} for d, v in daily.items()]
        summary = {"days": len(data), "total_revenue": round(sum(item["total"] for item in data), 2)}

        self._save_report("turnover_by_day", {}, summary, data)
        return ReportResult(summary, data)

    # Справка - най-продавани продукти
    def report_top_products(self):
        stats = {}
        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.OUT:
                continue
            product = self.product_controller.get_by_id(m.product_id)
            if not product: continue

            name = product.name
            if name not in stats:
                stats[name] = {"quantity": 0, "total": 0.0, "unit": product.unit}
            stats[name]["quantity"] += m.quantity
            stats[name]["total"] += m.quantity * m.price

        data = [{"product": name, "quantity": info["quantity"], "total": info["total"], "unit": info["unit"]}
                for name, info in stats.items()]
        data.sort(key=lambda x: x["quantity"], reverse=True)

        summary = {"total_products": len(data)}
        self._save_report("top_products", {}, summary, data)
        return ReportResult(summary, data)

    # Справка - обобщена наличност
    def report_inventory_summary(self):
        if not self.inventory_controller:
            summary = {"total_products": 0}
            self._save_report("inventory_summary", {}, summary, [])
            return ReportResult(summary, [])

        inv_data = self.inventory_controller.data or {}
        products_data = inv_data.get("products", {})
        data = []
        for product in self.product_controller.get_all():
            pid, unit = product.product_id, product.unit
            current_stock = self.inventory_controller.get_total_stock(pid)

            sold = 0
            for m in self.movement_controller.movements:
                if m.product_id == pid and m.movement_type == MovementType.OUT:
                    sold += m.quantity

            locations = products_data.get(pid, {}).get("locations", {})
            top3 = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:3]
            top3_str = ", ".join([f"{loc}:{qty}" for loc, qty in top3]) if top3 else "-"

            data.append({"product": product.name, "available": f"{current_stock} {unit}",
                         "sold": f"{sold} {unit}" if sold > 0 else "-", "top_locations": top3_str})

        summary = {"total_products": len(data)}
        self._save_report("inventory_summary", {}, summary, data)
        return ReportResult(summary, data)

    # Справка - жизнен цикъл на продукт
    def product_lifecycle(self, name):
        name_clean = name.lower()
        product = None
        for p in self.product_controller.get_all():
            if p.name and name_clean in p.name.lower():
                product = p
                break

        if product is None:
            summary = {"found": False}
            self._save_report("product_lifecycle", {"name": name}, summary, [])
            return None

        pid, unit = product.product_id, product.unit
        current_stock = self.inventory_controller.get_total_stock(pid)
        total_in = 0.0
        total_out = 0.0

        for m in self.movement_controller.movements:
            if m.product_id != pid: continue
            if m.movement_type == MovementType.IN:
                if m.supplier_id and m.user_id != "system" and "начално" not in m.description.lower():
                    total_in += m.quantity
            elif m.movement_type == MovementType.OUT:
                total_out += m.quantity

        initial_stock = current_stock + total_out - total_in
        data = {"product": product.name, "unit": unit,
                "initial_stock": initial_stock, "total_in": total_in,
                "total_out": total_out, "expected_stock": current_stock, "current_stock": current_stock,
                "revenue": round(total_out * product.price, 2)}

        summary = {"found": True}
        self._save_report("product_lifecycle", {"name": name}, summary, data)
        return data