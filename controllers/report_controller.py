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

    def _is_duplicate(self, old_report, new_report):
        return (old_report.get("report_type") == new_report.get("report_type") and
                old_report.get("parameters") == new_report.get("parameters") and
                old_report.get("data") == new_report.get("data"))

    def _save_report(self, report_type, parameters, summary, data):
        try:
            raw_data = self.repo.load()
            all_reports = raw_data if isinstance(raw_data, list) else []

            new_report_obj = Report(
                report_type=report_type,
                generated_on=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                parameters=parameters,
                data={"summary": summary, "data": data}
            )
            new_report_dict = new_report_obj.to_dict()

            for old in all_reports:
                if self._is_duplicate(old, new_report_dict):
                    return

            all_reports.append(new_report_dict)
            self.repo.save(all_reports)
        except Exception as e:
            print(f"Грешка при запис на отчет: {e}")

    def report_movements(self):
        data = []
        for m in self.movement_controller.movements:
            # Търсим продукта (get_by_id вече поддържа и двете дължини)
            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "-"
            mtype = m.movement_type.name

            if mtype == "IN":
                from_loc = "Доставчик"
                loc = self.location_controller.get_by_id(m.location_id)
                to_loc = loc.name if loc else m.location_id[:8]  # Показваме кратко, ако няма име

            elif mtype == "OUT":
                loc = self.location_controller.get_by_id(m.location_id)
                from_loc = loc.name if loc else m.location_id[:8]
                to_loc = m.customer or "Клиент"

            elif mtype == "MOVE":
                loc1 = self.location_controller.get_by_id(m.from_location_id)
                loc2 = self.location_controller.get_by_id(m.to_location_id)
                from_loc = loc1.name if loc1 else m.from_location_id[:8]
                to_loc = loc2.name if loc2 else m.to_location_id[:8]
            else:
                from_loc, to_loc = "-", "-"

            # За визуализация в отчета: подрязваме ID-тата
            data.append({
                "movement_id": m.movement_id[:8],
                "date": m.date[:10],
                "type": mtype,
                "product": product_name,
                "quantity": m.quantity,
                "unit": m.unit,
                "from": from_loc,
                "to": to_loc
            })

        summary = {"total": len(data)}
        self._save_report("movements_history", {}, summary, data)
        return ReportResult(summary, data)

    def report_sales(self):
        invoices = self.invoice_controller.get_all() or []
        data = []
        for inv in invoices:
            unit_price = float(inv.unit_price) if inv.unit_price else (inv.total_price / max(inv.quantity, 1))

            data.append({
                "invoice_number": inv.invoice_id[:8],
                "date": inv.date[:10],
                "client": inv.customer,
                "product": inv.product,
                "quantity": inv.quantity,
                "unit_price": round(unit_price, 2),
                "total_price": inv.total_price
            })

        summary = {"total_sales": len(data)}
        self._save_report("sales_all", {}, summary, data)
        return ReportResult(summary, data)

    def report_deliveries_all(self, keyword=None):
        data = []
        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.IN:
                continue

            product = self.product_controller.get_by_id(m.product_id)
            if not product: continue

            loc = self.location_controller.get_by_id(m.location_id)
            loc_name = loc.name if loc else m.location_id[:8]

            supplier_name = "-"
            if m.supplier_id:
                s = self.supplier_controller.get_by_id(m.supplier_id)
                supplier_name = s.name if s else m.supplier_id[:8]

            if keyword:
                k = keyword.lower()
                if k not in product.name.lower() and k not in supplier_name.lower() and k not in loc_name.lower():
                    continue

            data.append({
                "movement_id": m.movement_id[:8],
                "date": m.date[:10],
                "product": product.name,
                "quantity": m.quantity,
                "unit": m.unit,
                "price": float(m.price or 0),
                "supplier": supplier_name,
                "location": loc_name
            })

        summary = {"total": len(data)}
        self._save_report("deliveries_all", {"keyword": keyword}, summary, data)
        return ReportResult(summary, data)

    def report_inventory_summary(self):
        products = self.product_controller.get_all()
        data = []
        for p in products:
            pid = p.product_id  # Пълно ID за логиката
            stock = self.inventory_controller.get_total_stock(pid)

            # Изчисляваме продажбите по пълно ID
            sold = sum(m.quantity for m in self.movement_controller.movements
                       if str(m.product_id) == str(pid) and m.movement_type == MovementType.OUT)

            inv_entry = self.inventory_controller.data.get("products", {}).get(pid, {})
            locs = inv_entry.get("locations", {})
            # Показваме съкратени ID-та на локациите за прегледност
            top = sorted(locs.items(), key=lambda x: x[1], reverse=True)[:3]
            top_str = ", ".join([f"{lid[:8]}:{qty}" for lid, qty in top]) if top else "-"

            data.append({
                "product": p.name,
                "available": f"{stock} {p.unit}",
                "sold": f"{sold} {p.unit}" if sold > 0 else "-",
                "top_locations": top_str
            })

        summary = {"total_products": len(data)}
        self._save_report("inventory_summary", {}, summary, data)
        return ReportResult(summary, data)

    def product_lifecycle(self, name_or_id):
        # Вече поддържа търсене и по име, и по кратко ID
        product = self.product_controller.get_by_id(name_or_id)
        if not product:
            # Търсене по име, ако get_by_id не върне нищо (за по-стария стил)
            name_search = name_or_id.lower()
            for p in self.product_controller.get_all():
                if p.name and name_search in p.name.lower():
                    product = p
                    break

        if not product: return None

        pid = product.product_id  # Пълно UUID
        current_stock = self.inventory_controller.get_total_stock(pid)
        total_in, total_out, revenue, expense = 0.0, 0.0, 0.0, 0.0

        for m in self.movement_controller.movements:
            if str(m.product_id) != str(pid): continue
            qty = float(m.quantity or 0)

            if m.movement_type.name == "IN":
                total_in += qty
                expense += qty * float(m.price or 0)
            elif m.movement_type.name == "OUT":
                total_out += qty
                # Ако няма цена в движението, вземаме базовата цена на продукта
                price = float(m.price if m.price else product.price)
                revenue += qty * price

        fifo_cost = self.inventory_controller.calculate_fifo_cost(pid, self.movement_controller.movements,
                                                                  product.price)

        data = {
            "product": product.name,
            "product_id": pid[:8],
            "unit": product.unit,
            "total_in": total_in,
            "total_out": total_out,
            "current_stock": current_stock,
            "revenue": round(revenue, 2),
            "expense": round(expense, 2),
            "fifo_cost": round(fifo_cost, 2),
            "profit": round(revenue - fifo_cost, 2),
            "cash_balance": round(revenue - expense, 2)
        }

        summary = {"product": product.name}
        self._save_report("product_lifecycle", {"search": name_or_id}, summary, data)
        return data