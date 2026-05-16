from models.movement import MovementType
from datetime import datetime
from models.report import Report


class ReportController:
    def __init__(self, repo, product_controller, movement_controller, invoice_controller,
                 location_controller, inventory_controller, supplier_controller):

        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller




    def _match_string(self, target: str, keyword: str) -> bool:
        if not keyword:
            return True
        return keyword.lower().strip() in (target or "").lower()

    def _filter_movements_by_type(self, movements, m_type: str):
        """ Филтър по тип движение – IN, OUT или MOVE."""
        return [m for m in movements if m.movement_type.name == m_type.upper()]




    def report_inventory_full(self):
        data = self.inventory_controller._build_inventory()
        for item in data["products"]:
            product = None
            for p in self.product_controller.get_all():
                if p.name == item["product"]:
                    product = p
                    break

            if product is None:
                item.update({
                    "avg_in_price": "-", "avg_out_price": "-",
                    "expense": "-", "revenue": "-", "last_movement": "Няма"
                })
                continue

            pid = str(product.product_id)
            moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            in_prices = []
            out_prices = []
            total_expense = 0.0
            total_revenue = 0.0

            # Използваме вградения филтър
            in_moves = self._filter_movements_by_type(moves, "IN")
            out_moves = self._filter_movements_by_type(moves, "OUT")

            for m in in_moves:
                if m.price:
                    p_val, q_val = float(m.price), float(m.quantity)
                    in_prices.append(p_val)
                    total_expense += q_val * p_val

            for m in out_moves:
                if m.price:
                    p_val, q_val = float(m.price), float(m.quantity)
                    out_prices.append(p_val)
                    total_revenue += q_val * p_val

            item["avg_in_price"] = f"{sum(in_prices) / len(in_prices):.2f} лв." if in_prices else "-"
            item["avg_out_price"] = f"{sum(out_prices) / len(out_prices):.2f} лв." if out_prices else "-"
            item["expense"] = f"{total_expense:.2f} лв." if total_expense > 0 else "-"
            item["revenue"] = f"{total_revenue:.2f} лв." if total_revenue > 0 else "-"

            if moves:
                last = max(moves, key=lambda x: x.date)
                item["last_movement"] = f"{last.movement_type.name} - {str(last.date)[:19]}"
            else:
                item["last_movement"] = "Няма"

        return Report(report_type="Inventory Full", data=data["products"])

    def report_movements(self):
        rows = []
        for m in self.movement_controller.movements:
            loc = self.location_controller.get_by_id(m.location_id)
            rows.append({
                "date": str(m.date)[:10], "movement_id": m.movement_id[:8],
                "type": m.movement_type.name, "product": m.product_name,
                "quantity": m.quantity, "unit": m.unit,
                "from": "Склад" if m.movement_type.name == "OUT" else "Доставчик",
                "to": m.customer if m.movement_type.name == "OUT" else (loc.name if loc else "Склад")
            })
        return Report(report_type="Movement History", data=rows)

    def report_deliveries_all(self, keyword=""):
        # Използваме вградения филтър
        moves = self._filter_movements_by_type(self.movement_controller.movements, "IN")
        data = []
        for m in moves:
            sup = self.supplier_controller.get_by_id(m.supplier_id)
            supplier_name = sup.name if sup else "Неизвестен"

            # Използваме вградения _match_string
            if self._match_string(m.product_name, keyword) or self._match_string(supplier_name, keyword):
                data.append({
                    "date": str(m.date)[:10], "movement_id": m.movement_id[:8],
                    "product": m.product_name, "quantity": m.quantity, "unit": m.unit,
                    "price": m.price, "supplier": supplier_name
                })
        return Report(report_type="Deliveries", data=data)

    def report_sales(self):
        active = [i for i in self.invoice_controller.get_all() if i.is_active]
        data = [{
            "invoice_number": i.invoice_id[:8], "date": str(i.date)[:10],
            "client": i.customer, "product": i.product,
            "total_price": i.total_price, "status": "АКТИВНА"
        } for i in active]
        return Report(report_type="Sales", data=data)