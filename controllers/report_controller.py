from models.movement import MovementType
from datetime import datetime
from filters import report_filters


class ReportResult:
    # Малък контейнер за резултатите от справките
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
        # Превръщаме фактурите в удобни редове за показване
        rows = []
        for i in invoices:
            rows.append({
                "invoice_number": i.invoice_id[:8],
                "date": str(i.date)[:10],
                "client": i.customer,
                "product": i.product,
                "total_price": i.total_price
            })
        return rows

    def report_sales(self):
        # Обща справка за всички продажби
        invoices = self.invoice_controller.get_all() or []
        total_sum = 0.0

        for i in invoices:
            try:
                total_sum += float(i.total_price)
            except:
                pass

        summary = {
            "total_count": len(invoices),
            "total_revenue": round(total_sum, 2)
        }

        data = self._map_invoices_to_data(invoices)
        return ReportResult(summary, data)

    def report_sales_by_customer(self, customer_name: str):
        # Продажби за конкретен клиент
        invoices = self.invoice_controller.get_all() or []
        filtered = report_filters.filter_sales_by_customer(invoices, customer_name)

        summary = {"customer": customer_name, "count": len(filtered)}
        data = self._map_invoices_to_data(filtered)
        return ReportResult(summary, data)

    def report_sales_by_product(self, product_name: str):
        # Продажби за конкретен продукт
        invoices = self.invoice_controller.get_all() or []
        filtered = report_filters.filter_sales_by_product(invoices, product_name)

        summary = {"product": product_name, "count": len(filtered)}
        data = self._map_invoices_to_data(filtered)
        return ReportResult(summary, data)

    def report_movements(self):
        # Пълен списък на всички движения
        rows = []

        for m in self.movement_controller.movements:
            mtype = m.movement_type.name
            from_loc = "Няма"
            to_loc = "Няма"

            if mtype == "IN":
                from_loc = "Доставчик"
                loc = self.location_controller.get_by_id(m.location_id)
                to_loc = loc.name if loc else "Склад"

            elif mtype == "OUT":
                loc = self.location_controller.get_by_id(m.location_id)
                from_loc = loc.name if loc else "Склад"
                to_loc = m.customer or "Клиент"

            elif mtype == "MOVE":
                fl = self.location_controller.get_by_id(m.from_location_id)
                tl = self.location_controller.get_by_id(m.to_location_id)
                from_loc = fl.name if fl else "Източник"
                to_loc = tl.name if tl else "Цел"

            rows.append({
                "movement_id": m.movement_id[:8],
                "date": str(m.date)[:10],
                "type": mtype,
                "product": m.product_name,
                "quantity": m.quantity,
                "unit": m.unit,
                "from": from_loc,
                "to": to_loc
            })

        summary = {"total": len(rows)}
        return ReportResult(summary, rows)

    def report_deliveries_all(self, keyword=None):
        # Всички доставки (IN)
        all_moves = self.movement_controller.movements
        deliveries = report_filters.filter_movements_by_type(all_moves, "IN")

        rows = []

        for m in deliveries:
            sup = self.supplier_controller.get_by_id(m.supplier_id) if m.supplier_id else None
            supplier_name = sup.name if sup else "Неизвестен"

            if keyword:
                kw = keyword.lower()
                if kw not in m.product_name.lower() and kw not in supplier_name.lower():
                    continue

            rows.append({
                "movement_id": m.movement_id[:8],
                "date": str(m.date)[:10],
                "product": m.product_name,
                "quantity": m.quantity,
                "unit": m.unit,
                "price": float(m.price or 0),
                "supplier": supplier_name
            })

        summary = {"total": len(rows)}
        return ReportResult(summary, rows)

    def report_inventory_summary(self):
        # Обобщена справка за наличностите по локации
        rows = []

        for p in self.product_controller.get_all():
            pid = str(p.product_id)
            stock = self.inventory_controller.get_total_stock(pid)

            # Локации, в които има наличност
            loc_names = []
            inv_data = self.inventory_controller.data.get("products", {}).get(pid, {})

            for loc_id, qty in inv_data.get("locations", {}).items():
                if float(qty) > 0:
                    loc_obj = self.location_controller.get_by_id(loc_id)
                    loc_names.append(loc_obj.name if loc_obj else "Склад")

            loc_str = ", ".join(loc_names) if loc_names else "Няма наличност"

            sold = 0.0
            for m in self.movement_controller.movements:
                if str(m.product_id) == pid and m.movement_type.name == "OUT":
                    try:
                        sold += float(m.quantity)
                    except:
                        pass

            rows.append({
                "product": p.name,
                "available": f"{stock} {p.unit}",
                "sold": f"{sold} {p.unit}" if sold > 0 else "0",
                "top_locations": loc_str
            })

        summary = {"total": len(rows)}
        return ReportResult(summary, rows)

    def product_lifecycle(self, name_or_id):
        # Пълен жизнен цикъл на продукт
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
        moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

        total_in = sum(float(m.quantity) for m in moves if m.movement_type.name == "IN")
        total_out = sum(float(m.quantity) for m in moves if m.movement_type.name == "OUT")

        revenue = 0.0
        for m in moves:
            if m.movement_type.name == "OUT":
                revenue += float(m.quantity) * float(m.price or 0)

        fifo_cost = self.inventory_controller.calculate_fifo_cost(pid, self.movement_controller.movements, product.price)
        current_stock = self.inventory_controller.get_total_stock(pid)

        return {
            "product": product.name,
            "unit": product.unit,
            "total_in": total_in,
            "total_out": total_out,
            "current_stock": current_stock,
            "revenue": round(revenue, 2),
            "fifo_cost": round(fifo_cost, 2),
            "profit": round(revenue - fifo_cost, 2)
        }
