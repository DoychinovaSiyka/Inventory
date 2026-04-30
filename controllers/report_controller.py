from models.movement import MovementType
from models.report import Report
from datetime import datetime


class ReportResult:
    def __init__(self, summary, data):
        self.summary = summary
        self.data = data


class ReportController:
    def __init__(self, repo, product_controller, movement_controller, invoice_controller,
                 location_controller, inventory_controller, supplier_controller):

        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller

    # Проверка дали новият отчет е идентичен със стария
    def _is_duplicate(self, old_report, new_report):
        return (old_report.get("report_type") == new_report.get("report_type") and
                old_report.get("parameters") == new_report.get("parameters") and
                old_report.get("data") == new_report.get("data"))

    # Записваме отчет само ако е нов
    def _save_report(self, report_type, parameters, summary, data):
        try:
            raw_data = self.repo.load()
            if isinstance(raw_data, list):
                all_reports = raw_data
            else:
                all_reports = []

            # Подготвяме новия отчет
            new_report_obj = Report( report_type=report_type, generated_on=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                     parameters=parameters, data={"summary": summary, "data": data})
            new_report_dict = new_report_obj.to_dict()

            # 1) Ако вече има ИДЕНТИЧЕН отчет - НЕ записваме нищо
            for old in all_reports:
                if self._is_duplicate(old, new_report_dict):
                    return  # НИЩО не се променя
            # 2) Ако няма такъв - добавяме като НОВ
            all_reports.append(new_report_dict)

            # 3) Запис – сортирането е в save()
            self.repo.save(all_reports)

        except Exception as e:
            print(f"Грешка при запис на отчет: {e}")

    # Справка: всички движения
    def report_movements(self):
        data = []
        for m in self.movement_controller.movements:
            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "-"
            mtype = m.movement_type.name

            if mtype == "IN":
                from_loc = "Доставчик"
                loc = self.location_controller.get_by_id(m.location_id)
                to_loc = loc.name if loc else m.location_id

            elif mtype == "OUT":
                loc = self.location_controller.get_by_id(m.location_id)
                from_loc = loc.name if loc else m.location_id
                to_loc = m.customer or "Клиент"

            elif mtype == "MOVE":
                loc1 = self.location_controller.get_by_id(m.from_location_id)
                loc2 = self.location_controller.get_by_id(m.to_location_id)
                from_loc = loc1.name if loc1 else m.from_location_id
                to_loc = loc2.name if loc2 else m.to_location_id

            else:
                from_loc, to_loc = "-", "-"

            data.append({"movement_id": m.movement_id, "date": m.date[:10], "type": mtype,
                         "product": product_name, "quantity": m.quantity, "unit": m.unit,
                         "from": from_loc, "to": to_loc})

        summary = {"total": len(data)}
        self._save_report("movements_history", {}, summary, data)
        return ReportResult(summary, data)

    # Справка: всички продажби
    def report_sales(self):
        invoices = self.invoice_controller.get_all() or []
        data = [{"invoice_number": inv.invoice_id,
                 "date": inv.date[:10], "client": inv.customer,
                 "product": inv.product, "quantity": inv.quantity, "total_price": inv.total_price} for inv in invoices]

        summary = {"total_sales": len(data)}
        self._save_report("sales_all", {}, summary, data)
        return ReportResult(summary, data)

    # Справка: продажби по клиент
    def report_sales_by_customer(self, customer):
        invoices = self.invoice_controller.get_all() or []
        data = []
        for inv in invoices:
            if inv.customer and customer.lower() in inv.customer.lower():
                data.append({"invoice_number": inv.invoice_id, "date": inv.date[:10], "client": inv.customer,
                             "product": inv.product, "quantity": inv.quantity, "total_price": inv.total_price})
        summary = {"customer": customer, "total": len(data)}
        self._save_report("sales_by_customer", {"customer": customer}, summary, data)
        return ReportResult(summary, data)

    # Справка: продажби по продукт
    def report_sales_by_product(self, product):
        invoices = self.invoice_controller.get_all() or []
        data = []
        for inv in invoices:
            if inv.product and product.lower() in inv.product.lower():
                data.append({"invoice_number": inv.invoice_id, "date": inv.date[:10], "client": inv.customer,
                             "product": inv.product, "quantity": inv.quantity, "total_price": inv.total_price})
        summary = {"product": product, "total": len(data)}
        self._save_report("sales_by_product", {"product": product}, summary, data)
        return ReportResult(summary, data)

    # Справка: продажби по дата
    def report_sales_by_date(self, date_obj):
        date_str = date_obj.strftime("%Y-%m-%d")
        invoices = self.invoice_controller.get_all() or []
        data = []
        for inv in invoices:
            if inv.date and inv.date.startswith(date_str):
                data.append({"invoice_number": inv.invoice_id, "date": inv.date[:10], "client": inv.customer,
                             "product": inv.product, "quantity": inv.quantity, "total_price": inv.total_price})
        summary = {"date": date_str, "total": len(data)}
        self._save_report("sales_by_date", {"date": date_str}, summary, data)
        return ReportResult(summary, data)

    # Справка: всички доставки
    def report_deliveries_all(self, keyword=None):
        data = []
        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.IN:
                continue

            product = self.product_controller.get_by_id(m.product_id)
            if not product:
                continue
            loc = self.location_controller.get_by_id(m.location_id)
            loc_name = loc.name if loc else m.location_id

            supplier = "-"
            if self.supplier_controller and product.supplier_id:
                s = self.supplier_controller.get_by_id(product.supplier_id)
                supplier = s.name if s else product.supplier_id
            if keyword:
                k = keyword.lower()
                if k not in product.name.lower() and k not in supplier.lower() and k not in loc_name.lower():
                    continue

            data.append({"movement_id": m.movement_id, "date": m.date[:10], "product": product.name,
                         "quantity": m.quantity, "unit": m.unit, "supplier": supplier, "location": loc_name})

        summary = {"total": len(data)}
        report_type = "deliveries_all" if keyword is None else "deliveries_search"
        self._save_report(report_type, {"keyword": keyword}, summary, data)
        return ReportResult(summary, data)

    # Справка: оборот по дни
    def report_turnover_by_day(self):
        invoices = self.invoice_controller.get_all() or []
        daily = {}

        for inv in invoices:
            day = inv.date[:10]
            if day not in daily:
                daily[day] = {"count": 0, "total": 0}
            daily[day]["count"] += 1
            daily[day]["total"] += inv.total_price

        data = [{"date": d, "count": info["count"], "total": info["total"]} for d, info in daily.items()]
        summary = {"days": len(data)}
        self._save_report("turnover_by_day", {}, summary, data)
        return ReportResult(summary, data)

    # Справка: най-продавани продукти
    def report_top_products(self):
        stats = {}
        invoices = self.invoice_controller.get_all() or []

        for inv in invoices:
            name = inv.product
            if name not in stats:
                stats[name] = {"qty": 0, "total": 0, "unit": inv.unit}
            stats[name]["qty"] += inv.quantity
            stats[name]["total"] += inv.total_price

        data = [{"product": name, "quantity": info["qty"], "unit": info["unit"], "total": info["total"]}
                for name, info in stats.items()]

        summary = {"total_products": len(data)}
        self._save_report("top_products", {}, summary, data)
        return ReportResult(summary, data)

    # Справка: обобщена наличност
    def report_inventory_summary(self):
        products = self.product_controller.get_all()
        data = []

        for p in products:
            pid = p.product_id
            stock = self.inventory_controller.get_total_stock(pid)
            sold = sum(m.quantity for m in self.movement_controller.movements
                       if m.product_id == pid and m.movement_type == MovementType.OUT)

            inv_entry = self.inventory_controller.data.get("products", {}).get(pid, {})
            locs = inv_entry.get("locations", {})
            top = sorted(locs.items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ", ".join([f"{lid}:{qty}" for lid, qty in top]) if top else "-"

            data.append({"product": p.name, "available": f"{stock} {p.unit}",
                         "sold": f"{sold} {p.unit}" if sold > 0 else "-", "top_locations": top_str})

        summary = {"total_products": len(data)}
        self._save_report("inventory_summary", {}, summary, data)
        return ReportResult(summary, data)

    # Справка: жизнен цикъл на продукт
    def product_lifecycle(self, name):
        name_search = name.lower()
        product = None
        for p in self.product_controller.get_all():
            if p.name:
                if name_search in p.name.lower():
                    product = p
                    break

        if not product:
            return None

        pid = product.product_id
        current_stock = self.inventory_controller.get_total_stock(pid)

        total_in = 0.0
        total_out = 0.0
        revenue = 0.0
        expense = 0.0
        for m in self.movement_controller.movements:
            if m.product_id != pid:
                continue

            qty = float(m.quantity or 0)
            if m.movement_type.name == "IN":
                total_in += qty
                expense += qty * float(m.price or 0)

            elif m.movement_type.name == "OUT":
                total_out += qty
                price = float(m.price if m.price is not None else product.price)
                revenue += qty * price

        fifo_cost = self.inventory_controller.calculate_fifo_cost(pid, self.movement_controller.movements,
                                                                  product.price)

        data = {"product": product.name, "unit": product.unit, "total_in": total_in,
                 "total_out": total_out, "current_stock": current_stock, "revenue": revenue,
                 "expense": expense, "fifo_cost": fifo_cost, "profit": revenue - fifo_cost,
                 "cash_balance": revenue - expense}

        summary = {"product": product.name}
        self._save_report("product_lifecycle", {"search_name": name}, summary, data)
        return data
