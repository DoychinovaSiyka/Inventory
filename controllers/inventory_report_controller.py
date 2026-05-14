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


    #  ОБЕДИНЕН ОТЧЕТ ЗА НАЛИЧНОСТИТЕ
    def report_inventory_full(self):
        """Обединен отчет за наличностите."""

        data = self.inventory_controller._build_inventory()

        for item in data["products"]:
            product = None
            for p in self.product_controller.get_all():
                if p.name == item["product"]:
                    product = p
                    break

            if not product:
                item["avg_in_price"] = "0.00 лв."
                item["avg_out_price"] = "0.00 лв."
                item["last_move"] = "Няма"
                item["delivered"] = f"0 {item['unit']}"
                item["sold"] = f"0 {item['unit']}"
                continue

            pid = str(product.product_id)

            # Събираме всички движения за този продукт
            moves = []
            for m in self.movement_controller.movements:
                if str(m.product_id) == pid:
                    moves.append(m)


            in_prices = []
            for m in moves:
                if m.movement_type.name == "IN" and m.price:
                    in_prices.append(float(m.price))

            if in_prices:
                avg_in = sum(in_prices) / len(in_prices)
                item["avg_in_price"] = f"{avg_in:.2f} лв."
            else:
                item["avg_in_price"] = "0.00 лв."


            out_prices = []
            for m in moves:
                if m.movement_type.name == "OUT" and m.price:
                    out_prices.append(float(m.price))

            if out_prices:
                avg_out = sum(out_prices) / len(out_prices)
                item["avg_out_price"] = f"{avg_out:.2f} лв."
            else:
                item["avg_out_price"] = "0.00 лв."


            if moves:
                last_move = moves[0]
                for m in moves:
                    if m.date > last_move.date:
                        last_move = m
                item["last_move"] = f"{last_move.movement_type.name} - {str(last_move.date)[:10]}"
            else:
                item["last_move"] = "Няма"


            delivered = 0
            for m in moves:
                if m.movement_type.name == "IN":
                    delivered += float(m.quantity)
            item["delivered"] = f"{delivered} {item['unit']}"


            sold = 0
            for m in moves:
                if m.movement_type.name == "OUT":
                    sold += float(m.quantity)
            item["sold"] = f"{sold} {item['unit']}"

        return ReportResult(data["summary"], data["products"])

    #  ХРОНОЛОГИЯ НА ДВИЖЕНИЯТА
    def report_movements(self):
        rows = []

        for m in self.movement_controller.movements:
            loc = self.location_controller.get_by_id(m.location_id)
            rows.append({"date": str(m.date)[:10], "movement_id": m.movement_id[:8],
                         "type": m.movement_type.name,
                         "product": m.product_name, "quantity": m.quantity, "unit": m.unit,
                         "from": "Склад" if m.movement_type.name == "OUT" else "Доставчик",
                         "to": m.customer if m.movement_type.name == "OUT"
                         else (loc.name if loc else "Склад")})
        return ReportResult({"total": len(rows)}, rows)




    def report_deliveries_all(self, keyword=""):
        keyword = keyword.lower().strip()
        moves = [m for m in self.movement_controller.movements if m.movement_type.name == "IN"]

        data = []
        for m in moves:
            sup = self.supplier_controller.get_by_id(m.supplier_id)
            supplier_name = sup.name if sup else "Неизвестен"

            if keyword in m.product_name.lower() or keyword in supplier_name.lower():
                data.append({ "date": str(m.date)[:10], "movement_id": m.movement_id[:8],
                              "product": m.product_name,
                              "quantity": m.quantity, "unit": m.unit, "price": m.price,
                              "supplier": supplier_name})

        return ReportResult({"total": len(data)}, data)




    def report_sales(self):
        active = [i for i in self.invoice_controller.get_all() if i.is_active]

        data = [{"invoice_number": i.invoice_id[:8], "date": str(i.date)[:10], "client": i.customer,
                  "product": i.product, "total_price": i.total_price, "status": "АКТИВНА"} for i in active]

        return ReportResult({"total": len(active)}, data)




    def fifo_analysis_for_product(self, name_or_id):
        pid = self.inventory_controller._product_id(name_or_id)
        product = self.product_controller.get_by_id(pid)

        if not product:
            return None

        # Всички активни фактури за продукта
        invoices = [i for i in self.invoice_controller.get_all()
                    if i.is_active and i.product == product.name]

        total_out = sum(float(i.quantity) for i in invoices)
        revenue = sum(float(i.total_price) for i in invoices)

        fifo_cost = self.inventory_controller.calculate_fifo_cost(pid, self.movement_controller.movements, product.price)

        return {"product": product.name, "unit": product.unit,
                "total_out": total_out, "revenue": round(revenue, 2),
                "fifo_cost": fifo_cost, "profit": round(revenue - fifo_cost, 2)}
