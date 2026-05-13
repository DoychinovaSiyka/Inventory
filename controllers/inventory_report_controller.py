from models.movement import MovementType
from datetime import datetime
from filters import report_filters


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

    # нормализиране на short/long ID
    def _resolve_location(self, loc_id):
        if not loc_id:
            return None
        return self.location_controller.get_by_id(str(loc_id))

    def _map_invoices_to_data(self, invoices):
        rows = []
        for i in invoices:
            status = "АКТИВНА" if i.is_active else "АНУЛИРАНА"
            rows.append({
                "invoice_number": i.invoice_id[:8],
                "date": str(i.date)[:10],
                "client": i.customer,
                "product": i.product,
                "total_price": i.total_price,
                "status": status
            })
        return rows

    def _parse_number(self, value):
        if isinstance(value, (int, float)):
            return float(value)
        if not isinstance(value, str):
            return 0.0
        cleaned = "".join(ch for ch in value if ch.isdigit() or ch == ".")
        try:
            return float(cleaned)
        except:
            return 0.0

    # -----------------------------
    #   ПРОДАЖБИ
    # -----------------------------
    def report_sales(self):
        all_invoices = self.invoice_controller.get_all() or []
        active_invoices = [i for i in all_invoices if i.is_active]

        total_sum = sum(float(i.total_price) for i in active_invoices)

        summary = {
            "total_count": len(active_invoices),
            "total_revenue": round(total_sum, 2),
            "cancelled_count": len(all_invoices) - len(active_invoices)
        }

        data = self._map_invoices_to_data(active_invoices)
        return ReportResult(summary, data)

    def report_sales_by_customer(self, customer_name: str):
        invoices = self.invoice_controller.get_all() or []
        filtered = report_filters.filter_sales_by_customer(invoices, customer_name)

        summary = {"customer": customer_name, "count": len(filtered)}
        data = self._map_invoices_to_data(filtered)
        return ReportResult(summary, data)

    def report_sales_by_product(self, product_name: str):
        invoices = self.invoice_controller.get_all() or []
        filtered = report_filters.filter_sales_by_product(invoices, product_name)

        summary = {"product": product_name, "count": len(filtered)}
        data = self._map_invoices_to_data(filtered)
        return ReportResult(summary, data)

    # -----------------------------
    #   ДВИЖЕНИЯ
    # -----------------------------
    def report_movements(self):
        rows = []
        for m in self.movement_controller.movements:
            mtype = m.movement_type.name

            loc = self._resolve_location(m.location_id)
            fl = self._resolve_location(m.from_location_id)
            tl = self._resolve_location(m.to_location_id)

            if mtype == "IN":
                from_loc = "Доставчик"
                to_loc = loc.name if loc else "Склад"

            elif mtype == "OUT":
                from_loc = loc.name if loc else "Склад"
                to_loc = m.customer or "Клиент"

            else:  # MOVE
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

    # -----------------------------
    #   ДОСТАВКИ
    # -----------------------------
    def report_deliveries_all(self, keyword=None):
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

    def report_inventory_full(self):
        rows = []

        for p in self.product_controller.get_all():
            pid = str(p.product_id)

            total_stock = self.inventory_controller.get_total_stock(pid)
            if total_stock == 0:
                continue

            warehouse_map = {}
            inv_data = self.inventory_controller.data.get("products", {}).get(pid, {})
            for loc_id, qty in inv_data.get("locations", {}).items():
                qty = float(qty)
                if qty > 0:
                    loc = self._resolve_location(loc_id)
                    name = loc.name if loc else f"Склад {loc_id[:8]}"
                    warehouse_map[name] = qty

            moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            delivered_qty = sum(float(m.quantity) for m in moves if m.movement_type.name == "IN")
            delivered_prices = [float(m.price) for m in moves if m.movement_type.name == "IN"]
            avg_in_price = round(sum(delivered_prices) / len(delivered_prices), 2) if delivered_prices else None

            sold_qty = sum(float(m.quantity) for m in moves if m.movement_type.name == "OUT")
            sold_prices = [float(m.price) for m in moves if m.movement_type.name == "OUT"]
            avg_out_price = round(sum(sold_prices) / len(sold_prices), 2) if sold_prices else None

            if moves:
                last_move = max(moves, key=lambda x: x.date)
                last_move_str = f"{last_move.movement_type.name} – {str(last_move.date)[:10]}"
            else:
                last_move_str = "–"

            row = {
                "product": p.name,
                "unit": p.unit,
                "total": total_stock,
                "warehouses": warehouse_map,
                "delivered": delivered_qty,
                "sold": sold_qty,
                "avg_in_price": avg_in_price,
                "avg_out_price": avg_out_price,
                "last_move": last_move_str
            }

            rows.append(row)

        summary = {"total_products": len(rows)}

        # ❗ НИЩО НЕ ЗАПИСВАМЕ В JSON
        return ReportResult(summary, rows)
