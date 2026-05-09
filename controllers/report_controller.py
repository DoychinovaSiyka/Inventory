from models.movement import MovementType
from datetime import datetime
from filters import report_filters


class ReportResult:
    """Обект за връщане на резултати от справки (обобщение + детайли)."""

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

    def _map_invoices_to_data(self, invoices):
        """Превръща обектите фактури в списък за показване (редове)."""
        mapped = []
        for i in invoices:
            row = {"invoice_number": i.invoice_id[:8], "date": str(i.date)[:10],
                   "client": i.customer, "product": i.product,
                   "total_price": i.total_price}
            mapped.append(row)
        return mapped

    def report_sales(self):
        """Обща справка за всички продажби."""
        invoices = self.invoice_controller.get_all() or []
        total_sum = 0.0
        for i in invoices:
            try:
                total_sum += float(i.total_price)
            except Exception:
                continue

        summary = {"total_count": len(invoices), "total_revenue": round(total_sum, 2)}
        data = self._map_invoices_to_data(invoices)
        return ReportResult(summary, data)

    def report_sales_by_customer(self, customer_name: str):
        """Справка за продажби на конкретен клиент."""
        invoices = self.invoice_controller.get_all() or []
        filtered = report_filters.filter_sales_by_customer(invoices, customer_name)

        summary = {"customer": customer_name, "count": len(filtered)}
        data = self._map_invoices_to_data(filtered)
        return ReportResult(summary, data)

    def report_sales_by_product(self, product_name: str):
        """Справка за продажби на конкретен продукт."""
        invoices = self.invoice_controller.get_all() or []
        filtered = report_filters.filter_sales_by_product(invoices, product_name)

        summary = {"product": product_name, "count": len(filtered)}
        data = self._map_invoices_to_data(filtered)
        return ReportResult(summary, data)

    def report_movements(self):
        """Пълна хронология на всички складови движения."""
        data = []
        for m in self.movement_controller.movements:
            mtype = m.movement_type.name
            f_loc, t_loc = "Няма", "Няма"

            if mtype == "IN":
                f_loc = "Доставчик"
                loc = self.location_controller.get_by_id(m.location_id)
                t_loc = loc.name if loc else "Склад"
            elif mtype == "OUT":
                loc = self.location_controller.get_by_id(m.location_id)
                f_loc = loc.name if loc else "Склад"
                t_loc = m.customer or "Клиент"
            elif mtype == "MOVE":
                fl = self.location_controller.get_by_id(m.from_location_id)
                tl = self.location_controller.get_by_id(m.to_location_id)
                f_loc = fl.name if fl else "Източник"
                t_loc = tl.name if tl else "Цел"

            row = {"movement_id": m.movement_id[:8], "date": str(m.date)[:10],
                   "type": mtype, "product": m.product_name, "quantity": m.quantity,
                   "unit": m.unit, "from": f_loc, "to": t_loc}
            data.append(row)

        summary = {"total": len(data)}
        return ReportResult(summary, data)

    def report_deliveries_all(self, keyword=None):
        """Справка за всички доставки (Зареждания)."""
        all_m = self.movement_controller.movements
        deliveries = report_filters.filter_movements_by_type(all_m, "IN")

        data = []
        for m in deliveries:
            sup = self.supplier_controller.get_by_id(m.supplier_id) if m.supplier_id else None
            s_name = sup.name if sup else "Неизвестен"

            if keyword:
                kw = keyword.lower()
                if kw not in m.product_name.lower() and kw not in s_name.lower():
                    continue

            data.append({"movement_id": m.movement_id[:8], "date": str(m.date)[:10],
                         "product": m.product_name, "quantity": m.quantity, "unit": m.unit,
                         "price": float(m.price or 0), "supplier": s_name})

        summary = {"total": len(data)}
        return ReportResult(summary, data)

    def report_inventory_summary(self):
        """Обобщена справка за наличности с реални локации."""
        data = []
        for p in self.product_controller.get_all():
            pid = str(p.product_id)
            stock = self.inventory_controller.get_total_stock(pid)

            # Намираме имената на локациите, където има наличност > 0
            loc_names = []
            inv_data = self.inventory_controller.data.get("products", {}).get(pid, {})
            for loc_id, qty in inv_data.get("locations", {}).items():
                if float(qty) > 0:
                    loc_obj = self.location_controller.get_by_id(loc_id)
                    loc_names.append(loc_obj.name if loc_obj else "Склад")

            top_locs = ", ".join(loc_names) if loc_names else "Няма наличност"

            sold = 0.0
            for m in self.movement_controller.movements:
                if str(m.product_id) == pid and m.movement_type.name == "OUT":
                    try:
                        sold += float(m.quantity)
                    except Exception:
                        continue

            row = {"product": p.name, "available": f"{stock} {p.unit}",
                   "sold": f"{sold} {p.unit}" if sold > 0 else "0",
                   "top_locations": top_locs}
            data.append(row)

        summary = {"total": len(data)}
        return ReportResult(summary, data)

    def product_lifecycle(self, name_or_id):
        """Пълен жизнен цикъл на продукт: Приходи, Разходи, Печалба."""
        product = self.product_controller.get_by_id(name_or_id)
        if not product:
            search = str(name_or_id).lower()
            for p in self.product_controller.get_all():
                if search in p.name.lower():
                    product = p
                    break

        if not product:
            return None

        pid = str(product.product_id)
        prod_moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

        t_in = sum(float(m.quantity) for m in prod_moves if m.movement_type.name == "IN")
        t_out = sum(float(m.quantity) for m in prod_moves if m.movement_type.name == "OUT")

        rev = 0.0
        for m in prod_moves:
            if m.movement_type.name == "OUT":
                rev += float(m.quantity) * float(m.price or 0)

        cost = self.inventory_controller.calculate_fifo_cost(pid, self.movement_controller.movements, product.price)
        current_stock = self.inventory_controller.get_total_stock(pid)

        return {"product": product.name, "unit": product.unit, "total_in": t_in,
                "total_out": t_out, "current_stock": current_stock, "revenue": round(rev, 2),
                "fifo_cost": round(cost, 2), "profit": round(rev - cost, 2)}