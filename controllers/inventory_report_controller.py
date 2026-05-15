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

    # Взимаме всички движения за продукт
    def _get_product_moves(self, pid):
        return [m for m in self.movement_controller.movements if str(m.product_id) == pid]



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
            moves = self._get_product_moves(pid)

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




    def full_product_report(self, product_id):
        product = self.product_controller.get_by_id(product_id)
        if not product:
            return None

        movements = [m for m in self.movement_controller.movements if str(m.product_id) == str(product_id)]
        movements.sort(key=lambda x: x.date)

        history = []
        running_total = 0

        for mv in movements:
            entry = {"date": mv.date, "type": mv.movement_type.name, "qty": mv.quantity, "before": running_total}

            if mv.movement_type.name in ("IN", "OUT"):
                running_total += mv.quantity if mv.movement_type.name == "IN" else -mv.quantity
                loc = self.location_controller.get_by_id(mv.location_id)
                entry["location"] = loc.name if loc else "Неизвестен склад"

            elif mv.movement_type.name == "MOVE":
                from_loc = self.location_controller.get_by_id(mv.from_location_id)
                to_loc = self.location_controller.get_by_id(mv.to_location_id)
                entry["from"] = from_loc.name if from_loc else "?"
                entry["to"] = to_loc.name if to_loc else "?"

            entry["after"] = running_total
            history.append(entry)

        inventory = self.inventory_controller._build_inventory()
        product_row = next((p for p in inventory["products"] if p["product"] == product.name), None)

        total_in = sum(m.quantity for m in movements if m.movement_type.name == "IN")
        total_out = sum(m.quantity for m in movements if m.movement_type.name == "OUT")

        in_prices = [float(m.price) for m in movements if m.movement_type.name == "IN" and m.price]
        out_prices = [float(m.price) for m in movements if m.movement_type.name == "OUT" and m.price]

        avg_in_price = sum(in_prices) / len(in_prices) if in_prices else 0
        avg_out_price = sum(out_prices) / len(out_prices) if out_prices else 0

        fifo_cost = self.inventory_controller.calculate_fifo_cost(product_id, movements)
        revenue = total_out * avg_out_price if avg_out_price else 0
        profit = revenue - fifo_cost

        return {"product": product.name, "unit": product.unit, "history": history, "final_total": running_total,
                "warehouses": product_row["warehouses"] if product_row else {}, "delivered": total_in, "sold": total_out,
                "avg_in": avg_in_price, "avg_out": avg_out_price, "fifo_cost": fifo_cost,
                "revenue": revenue, "profit": profit, "last_movement": history[-1] if history else None}
