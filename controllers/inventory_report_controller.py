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
        """Помощен метод за преобразуване на фактури в речници за справки."""
        rows = []
        for i in invoices:
            status = "АКТИВНА" if i.is_active else "АНУЛИРАНА"
            rows.append({"invoice_number": i.invoice_id[:8], "date": str(i.date)[:10],
                         "client": i.customer, "product": i.product, "total_price": i.total_price, "status": status})
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

    # Обща справка за всички продажби
    def report_sales(self):
        all_invoices = self.invoice_controller.get_all() or []
        active_invoices = [i for i in all_invoices if i.is_active]

        total_sum = 0.0
        for i in active_invoices:
            try:
                total_sum += float(i.total_price)
            except:
                pass

        summary = {"total_count": len(active_invoices), "total_revenue": round(total_sum, 2),
                   "cancelled_count": len(all_invoices) - len(active_invoices)}

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

    def report_movements(self):
        rows = []
        for m in self.movement_controller.movements:
            mtype = m.movement_type.name

            # нормализиране на ID-тата
            loc = self._resolve_location(m.location_id)
            fl = self._resolve_location(m.from_location_id)
            tl = self._resolve_location(m.to_location_id)

            from_loc = "Няма"
            to_loc = "Няма"

            if mtype == "IN":
                from_loc = "Доставчик"
                to_loc = loc.name if loc else "Склад"

            elif mtype == "OUT":
                from_loc = loc.name if loc else "Склад"
                to_loc = m.customer or "Клиент"

            elif mtype == "MOVE":
                from_loc = fl.name if fl else "Източник"
                to_loc = tl.name if tl else "Цел"

            rows.append({"movement_id": m.movement_id[:8], "date": str(m.date)[:10], "type": mtype,
                         "product": m.product_name, "quantity": m.quantity,
                         "unit": m.unit, "from": from_loc, "to": to_loc})

        summary = {"total": len(rows)}
        return ReportResult(summary, rows)

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

            rows.append({"movement_id": m.movement_id[:8], "date": str(m.date)[:10],
                         "product": m.product_name, "quantity": m.quantity, "unit": m.unit,
                         "price": float(m.price or 0), "supplier": supplier_name})

        summary = {"total": len(rows)}
        return ReportResult(summary, rows)

    def product_lifecycle(self, name_or_id):
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

        active_invoices = [i for i in self.invoice_controller.get_all() if i.is_active and i.product == product.name]
        total_out = sum(float(i.quantity) for i in active_invoices)
        revenue = sum(float(i.total_price) for i in active_invoices)

        fifo_cost = self.inventory_controller.calculate_fifo_cost(pid, self.movement_controller.movements,
                                                                  product.price)
        current_stock = self.inventory_controller.get_total_stock(pid)

        return {"product": product.name, "unit": product.unit,
                "total_in": total_in, "total_out": total_out, "current_stock": current_stock,
                "revenue": round(revenue, 2),
                "fifo_cost": round(fifo_cost, 2), "profit": round(revenue - fifo_cost, 2)}

    def report_inventory_full(self):
        """Обединен отчет за наличностите: Общо количество, Разпределение по складове, Доставено / Продадено, Средни цени,
        Последно движение """

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
                    loc = self._resolve_location(loc_id)   # ← НОВО
                    name = loc.name if loc else f"Склад {loc_id[:8]}"
                    warehouse_map[name] = qty

            warehouse_str = ", ".join(f"{k}: {v} {p.unit}" for k, v in warehouse_map.items()) \
                if warehouse_map else "–"

            moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            delivered_qty = sum(float(m.quantity) for m in moves if m.movement_type.name == "IN")
            delivered_str = f"{delivered_qty} {p.unit}" if delivered_qty > 0 else "–"

            delivered_prices = [float(m.price) for m in moves if m.movement_type.name == "IN"]
            avg_in_price = round(sum(delivered_prices) / len(delivered_prices), 2) if delivered_prices else None
            avg_in_str = f"{avg_in_price} лв." if avg_in_price else "–"

            sold_qty = sum(float(m.quantity) for m in moves if m.movement_type.name == "OUT")
            sold_str = f"{sold_qty} {p.unit}" if sold_qty > 0 else "–"

            sold_prices = [float(m.price) for m in moves if m.movement_type.name == "OUT"]
            avg_out_price = round(sum(sold_prices) / len(sold_prices), 2) if sold_prices else None
            avg_out_str = f"{avg_out_price} лв." if avg_out_price else "–"

            if moves:
                last_move = max(moves, key=lambda x: x.date)
                last_move_str = f"{last_move.movement_type.name} – {str(last_move.date)[:10]}"
            else:
                last_move_str = "–"

            rows.append({"product": p.name, "total": f"{total_stock} {p.unit}", "warehouses": warehouse_str,
                         "delivered": delivered_str, "sold": sold_str, "avg_in_price": avg_in_str,
                         "avg_out_price": avg_out_str, "last_move": last_move_str})

        summary = {"total_products": len(rows)}
        return ReportResult(summary, rows)
