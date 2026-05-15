from models.movement import MovementType
from datetime import datetime


class ReportResult:
    def __init__(self, summary, data):
        self.summary = summary
        self.data = data


class ReportController:
    def __init__(self, repo, product_controller, movement_controller, invoice_controller,
                 location_controller, inventory_controller, supplier_controller):

        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller




    # ОБЕДИНЕН ОТЧЕТ ЗА НАЛИЧНОСТИТЕ
    def report_inventory_full(self):
        data = self.inventory_controller._build_inventory()

        for item in data["products"]:

            product = None
            for p in self.product_controller.get_all():
                if p.name == item["product"]:
                    product = p
                    break


            if product is None:
                item["avg_in_price"] = "-"
                item["avg_out_price"] = "-"
                item["expense"] = "-"
                item["revenue"] = "-"
                item["last_movement"] = "Няма"
                continue

            pid = str(product.product_id)
            moves = []
            for m in self.movement_controller.movements:
                if str(m.product_id) == pid:
                    moves.append(m)


            in_prices = []
            out_prices = []

            for m in moves:
                if m.movement_type.name == "IN" and m.price:
                    in_prices.append(float(m.price))
                elif m.movement_type.name == "OUT" and m.price:
                    out_prices.append(float(m.price))

            if len(in_prices) > 0:
                avg_in = sum(in_prices) / len(in_prices)
            else:
                avg_in = 0.0

            if len(out_prices) > 0:
                avg_out = sum(out_prices) / len(out_prices)
            else:
                avg_out = 0.0


            item["avg_in_price"] = f"{avg_in:.2f} лв." if avg_in > 0 else "-"
            item["avg_out_price"] = f"{avg_out:.2f} лв." if avg_out > 0 else "-"
            delivered = 0
            sold = 0

            for m in moves:
                if m.movement_type.name == "IN":
                    delivered += m.quantity
                elif m.movement_type.name == "OUT":
                    sold += m.quantity


            expense = self.inventory_controller.calculate_fifo_cost(pid, moves, fallback_price=avg_in)
            item["expense"] = f"{expense:.2f} лв." if expense > 0 else "-"


            revenue = sold * avg_out
            item["revenue"] = f"{revenue:.2f} лв." if revenue > 0 else "-"


            if len(moves) > 0:
                last = moves[0]
                for m in moves:
                    if m.date > last.date:
                        last = m
                item["last_movement"] = f"{last.movement_type.name} - {str(last.date)[:19]}"
            else:
                item["last_movement"] = "Няма"

        return ReportResult(data["summary"], data["products"])




    def report_movements(self):
        rows = []

        for m in self.movement_controller.movements:
            loc = self.location_controller.get_by_id(m.location_id)

            rows.append({"date": str(m.date)[:10], "movement_id": m.movement_id[:8], "type": m.movement_type.name,
                         "product": m.product_name, "quantity": m.quantity, "unit": m.unit,
                         "from": "Склад" if m.movement_type.name == "OUT" else "Доставчик",
                         "to": m.customer if m.movement_type.name == "OUT" else (loc.name if loc else "Склад")})

        return ReportResult({"total": len(rows)}, rows)





    def report_deliveries_all(self, keyword=""):
        keyword = keyword.lower().strip()
        moves = [m for m in self.movement_controller.movements if m.movement_type.name == "IN"]

        data = []
        for m in moves:
            sup = self.supplier_controller.get_by_id(m.supplier_id)
            supplier_name = sup.name if sup else "Неизвестен"

            if keyword in m.product_name.lower() or keyword in supplier_name.lower():
                data.append({"date": str(m.date)[:10], "movement_id": m.movement_id[:8],
                             "product": m.product_name, "quantity": m.quantity, "unit": m.unit,
                             "price": m.price, "supplier": supplier_name})

        return ReportResult({"total": len(data)}, data)




    def report_sales(self):
        active = [i for i in self.invoice_controller.get_all() if i.is_active]

        data = [{"invoice_number": i.invoice_id[:8], "date": str(i.date)[:10], "client": i.customer,
                  "product": i.product, "total_price": i.total_price, "status": "АКТИВНА"} for i in active]

        return ReportResult({"total": len(active)}, data)
