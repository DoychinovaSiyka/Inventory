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
            product = next((p for p in self.product_controller.get_all()
                            if p.name == item["product"]), None)

            if not product:
                item["avg_in_price"] = "0.00 лв."
                item["avg_out_price"] = "0.00 лв."
                item["last_move"] = "Няма"
                item["delivered"] = f"0 {item['unit']}"
                item["sold"] = f"0 {item['unit']}"
                continue

            pid = str(product.product_id)
            moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

            # Средни цени
            in_prices = [float(m.price) for m in moves if m.movement_type.name == "IN" and m.price]
            out_prices = [float(m.price) for m in moves if m.movement_type.name == "OUT" and m.price]

            item["avg_in_price"] = f"{(sum(in_prices) / len(in_prices)):.2f} лв." if in_prices else "0.00 лв."
            item["avg_out_price"] = f"{(sum(out_prices) / len(out_prices)):.2f} лв." if out_prices else "0.00 лв."

            # Последно движение
            last = max(moves, key=lambda x: x.date) if moves else None
            item["last_move"] = f"{last.movement_type.name} - {str(last.date)[:10]}" if last else "Няма"

            # Доставено / Продадено
            delivered = sum(m.quantity for m in moves if m.movement_type.name == "IN")
            sold = sum(m.quantity for m in moves if m.movement_type.name == "OUT")

            item["delivered"] = f"{delivered} {item['unit']}"
            item["sold"] = f"{sold} {item['unit']}"

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
