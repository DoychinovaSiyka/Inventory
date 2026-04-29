from models.movement import MovementType
from models.report import Report
from datetime import datetime


class ReportResult:
    def __init__(self, summary, data):
        self.summary = summary
        self.data = data


class ReportController:
    def __init__(self, repo, product_controller, movement_controller,
                 invoice_controller, location_controller, inventory_controller,
                 supplier_controller):

        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller

    # вътрешно: запис на отчет
    def _save_report(self, report_type, parameters, summary, data):
        report = Report(
            report_type=report_type,
            generated_on=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            parameters=parameters,
            data={"summary": summary, "data": data}
        )

        all_reports = self.repo.get_all() or []
        all_reports.append(report.to_dict())
        self.repo.save(all_reports)

    # ---------------------------------------------------------
    # 1) Движения
    # ---------------------------------------------------------
    def report_movements(self):
        data = []

        for m in self.movement_controller.movements:
            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "-"

            # Нормализиран тип: IN / OUT / MOVE
            mtype = m.movement_type.name

            # Логика за "От" и "Към"
            if mtype == "IN":
                from_loc = "Доставчик"
                loc = self.location_controller.get_by_id(m.location_id)
                to_loc = loc.name if loc else m.location_id

            elif mtype == "OUT":
                loc = self.location_controller.get_by_id(m.location_id)
                from_loc = loc.name if loc else m.location_id
                to_loc = m.customer or "Клиент"

            elif mtype == "MOVE":
                loc_from = self.location_controller.get_by_id(m.from_location_id)
                loc_to = self.location_controller.get_by_id(m.to_location_id)
                from_loc = loc_from.name if loc_from else m.from_location_id
                to_loc = loc_to.name if loc_to else m.to_location_id

            else:
                from_loc = "-"
                to_loc = "-"

            data.append({
                "movement_id": m.movement_id,
                "date": m.date[:10],
                "type": mtype,  # ← ВАЖНО! Вече е "IN", "OUT", "MOVE"
                "product": product_name,
                "quantity": m.quantity,
                "unit": m.unit,
                "from": from_loc,  # ← ВАЖНО! View го очаква
                "to": to_loc  # ← ВАЖНО! View го очаква
            })

        summary = {"total": len(data)}
        self._save_report("movements", {}, summary, data)
        return ReportResult(summary, data)

    # ---------------------------------------------------------
    # 2) Всички продажби
    # ---------------------------------------------------------
    def report_sales(self):
        invoices = self.invoice_controller.get_all() or []
        data = []

        for inv in invoices:
            data.append({
                "invoice_number": inv.invoice_id,
                "date": inv.date[:10],
                "client": inv.customer,
                "product": inv.product,
                "quantity": inv.quantity,
                "total_price": inv.total_price
            })

        summary = {"total_sales": len(data)}
        self._save_report("sales", {}, summary, data)
        return ReportResult(summary, data)

    # ---------------------------------------------------------
    # 3) Продажби по клиент
    # ---------------------------------------------------------
    def report_sales_by_customer(self, customer):
        customer = customer.lower()
        invoices = self.invoice_controller.get_all() or []
        data = []

        for inv in invoices:
            if inv.customer and customer in inv.customer.lower():
                data.append({
                    "invoice_number": inv.invoice_id,
                    "date": inv.date[:10],
                    "client": inv.customer,
                    "product": inv.product,
                    "quantity": inv.quantity,
                    "total_price": inv.total_price
                })

        summary = {"customer": customer, "total": len(data)}
        self._save_report("sales_by_customer", {"customer": customer}, summary, data)
        return ReportResult(summary, data)

    # ---------------------------------------------------------
    # 4) Продажби по продукт
    # ---------------------------------------------------------
    def report_sales_by_product(self, product):
        product = product.lower()
        invoices = self.invoice_controller.get_all() or []
        data = []

        for inv in invoices:
            if inv.product and product in inv.product.lower():
                data.append({
                    "invoice_number": inv.invoice_id,
                    "date": inv.date[:10],
                    "client": inv.customer,
                    "product": inv.product,
                    "quantity": inv.quantity,
                    "total_price": inv.total_price
                })

        summary = {"product": product, "total": len(data)}
        self._save_report("sales_by_product", {"product": product}, summary, data)
        return ReportResult(summary, data)

    # ---------------------------------------------------------
    # 5) Продажби по дата
    # ---------------------------------------------------------
    def report_sales_by_date(self, date_obj):
        date_str = date_obj.strftime("%Y-%m-%d")
        invoices = self.invoice_controller.get_all() or []
        data = []

        for inv in invoices:
            if inv.date and inv.date.startswith(date_str):
                data.append({
                    "invoice_number": inv.invoice_id,
                    "date": inv.date[:10],
                    "client": inv.customer,
                    "product": inv.product,
                    "quantity": inv.quantity,
                    "total_price": inv.total_price
                })

        summary = {"date": date_str, "total": len(data)}
        self._save_report("sales_by_date", {"date": date_str}, summary, data)
        return ReportResult(summary, data)

    # ---------------------------------------------------------
    # 6) Доставки (IN)
    # ---------------------------------------------------------
    def report_deliveries_all(self, keyword=None):
        data = []

        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.IN:
                continue

            product = self.product_controller.get_by_id(m.product_id)
            if not product:
                continue

            product_name = product.name

            # ОПРАВЕНО: IN движение използва location_id
            loc = self.location_controller.get_by_id(m.location_id)
            loc_name = loc.name if loc else m.location_id

            supplier = "-"
            if self.supplier_controller and product.supplier_id:
                s = self.supplier_controller.get_by_id(product.supplier_id)
                supplier = s.name if s else product.supplier_id

            row = {
                "movement_id": m.movement_id,
                "date": m.date[:10],
                "product": product_name,
                "quantity": m.quantity,
                "unit": m.unit,
                "supplier": supplier,
                "location": loc_name
            }

            if keyword:
                k = keyword.lower()
                if k not in product_name.lower() and k not in supplier.lower() and k not in loc_name.lower():
                    continue

            data.append(row)

        summary = {"total": len(data)}
        self._save_report("deliveries_all", {"keyword": keyword}, summary, data)
        return ReportResult(summary, data)

    # ---------------------------------------------------------
    # 7) Оборот по дни
    # ---------------------------------------------------------
    def report_turnover_by_day(self):
        invoices = self.invoice_controller.get_all() or []
        daily = {}

        for inv in invoices:
            day = inv.date[:10]
            if day not in daily:
                daily[day] = {"count": 0, "total": 0}
            daily[day]["count"] += 1
            daily[day]["total"] += inv.total_price

        data = []
        for day, info in daily.items():
            data.append({"date": day, "count": info["count"], "total": info["total"]})

        summary = {"days": len(data)}
        self._save_report("turnover_by_day", {}, summary, data)
        return ReportResult(summary, data)

    # ---------------------------------------------------------
    # 8) Най-продавани продукти
    # ---------------------------------------------------------
    def report_top_products(self):
        stats = {}
        invoices = self.invoice_controller.get_all() or []

        for inv in invoices:
            name = inv.product
            if name not in stats:
                stats[name] = {"qty": 0, "total": 0, "unit": inv.unit}
            stats[name]["qty"] += inv.quantity
            stats[name]["total"] += inv.total_price

        data = []
        for name, info in stats.items():
            data.append({
                "product": name,
                "quantity": info["qty"],
                "unit": info["unit"],
                "total": info["total"]
            })

        summary = {"total_products": len(data)}
        self._save_report("top_products", {}, summary, data)
        return ReportResult(summary, data)

    # ---------------------------------------------------------
    # 9) Обобщена наличност
    # ---------------------------------------------------------
    def report_inventory_summary(self):
        products = self.product_controller.get_all()
        data = []

        for p in products:
            pid = p.product_id
            stock = self.inventory_controller.get_total_stock(pid)

            sold = 0
            for m in self.movement_controller.movements:
                if m.product_id == pid and m.movement_type == MovementType.OUT:
                    sold += m.quantity

            inv_entry = self.inventory_controller.data.get("products", {}).get(pid, {})
            locs = inv_entry.get("locations", {})
            top = sorted(locs.items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ", ".join([f"{lid}:{qty}" for lid, qty in top]) if top else "-"

            data.append({
                "product": p.name,
                "available": f"{stock} {p.unit}",
                "sold": f"{sold} {p.unit}" if sold > 0 else "-",
                "top_locations": top_str
            })

        summary = {"total_products": len(data)}
        self._save_report("inventory_summary", {}, summary, data)
        return ReportResult(summary, data)


    # 10) Жизнен цикъл
    # ---------------------------------------------------------
    def product_lifecycle(self, name):
        name = name.lower()
        product = None

        # намираме продукта
        for p in self.product_controller.get_all():
            if p.name and name in p.name.lower():
                product = p
                break

        if not product:
            return None

        pid = product.product_id
        unit = product.unit

        # текущо количество от инвентара
        current_stock = self.inventory_controller.get_total_stock(pid)

        total_in = 0.0
        total_out_qty = 0.0
        revenue = 0.0

        # събираме IN, OUT и приход
        for m in self.movement_controller.movements:
            if m.product_id != pid:
                continue

            if m.movement_type == MovementType.IN:
                total_in += float(m.quantity or 0)

            elif m.movement_type == MovementType.OUT:
                qty = float(m.quantity or 0)
                price = float(m.price if m.price is not None else product.price)
                total_out_qty += qty
                revenue += qty * price

        # начално количество
        initial_stock = current_stock + total_out_qty - total_in

        # FIFO разход (себестойност)
        cost = self.inventory_controller.calculate_fifo_cost(
            pid,
            self.movement_controller.movements,
            fallback_price=product.price
        )

        # печалба и марж
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue > 0 else 0.0

        data = {
            "product": product.name,
            "unit": unit,
            "initial_stock": initial_stock,
            "total_in": total_in,
            "total_out": total_out_qty,
            "current_stock": current_stock,
            "revenue": revenue,
            "cost": cost,
            "profit": profit,
            "margin": margin
        }

        summary = {"found": True}
        self._save_report("product_lifecycle", {"name": name}, summary, data)
        return data
