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
        """Взима актуалните данни от инвентарния контролер."""
        inv_data = self.inventory_controller._build_inventory()

        for item in inv_data["products"]:
            # Намираме обекта на продукта по име
            p_obj = next((p for p in self.product_controller.get_all() if p.name == item["product"]), None)
            if p_obj:
                pid = str(p_obj.product_id)
                # Филтрираме всички движения за този продукт
                moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]

                # Средна входна цена
                in_prices = [float(m.price) for m in moves if m.movement_type.name == "IN" and m.price]
                item["avg_in_price"] = f"{round(sum(in_prices) / len(in_prices), 2):.2f} лв." if in_prices else "0.00 лв."

                # ОПРАВЕНО: Добавена средна изходна цена (за да не гърми ReportsView)
                out_prices = [float(m.price) for m in moves if m.movement_type.name == "OUT" and m.price]
                item["avg_out_price"] = f"{round(sum(out_prices) / len(out_prices), 2):.2f} лв." if out_prices else "0.00 лв."

                # Последно движение
                last = max(moves, key=lambda x: x.date) if moves else None
                item["last_move"] = f"{last.movement_type.name} - {str(last.date)[:10]}" if last else "Няма"

                # Общи количества
                item["delivered"] = f"{sum(float(m.quantity) for m in moves if m.movement_type.name == 'IN')} {item['unit']}"
                item["sold"] = f"{sum(float(m.quantity) for m in moves if m.movement_type.name == 'OUT')} {item['unit']}"
            else:
                item["avg_in_price"] = "0.00 лв."
                item["avg_out_price"] = "0.00 лв."
                item["last_move"] = "Няма"
                item["delivered"] = "0"
                item["sold"] = "0"

        return ReportResult(inv_data["summary"], inv_data["products"])

    # ХРОНОЛОГИЯ НА ДВИЖЕНИЯТА
    def report_movements(self):
        rows = []
        for m in self.movement_controller.movements:
            loc = self.location_controller.get_by_id(m.location_id)
            rows.append({
                "date": str(m.date)[:10],
                "movement_id": m.movement_id[:8],
                "type": m.movement_type.name,
                "product": m.product_name,
                "quantity": m.quantity,
                "unit": m.unit,
                "from": "Склад" if m.movement_type.name == "OUT" else "Доставчик",
                "to": m.customer if m.movement_type.name == "OUT" else (loc.name if loc else "Склад")
            })
        return ReportResult({"total": len(rows)}, rows)

    # ВСИЧКИ ДОСТАВКИ
    def report_deliveries_all(self, keyword=""):
        moves = [m for m in self.movement_controller.movements if m.movement_type.name == "IN"]
        data = []

        for m in moves:
            sup = self.supplier_controller.get_by_id(m.supplier_id)
            s_name = sup.name if sup else "Неизвестен"

            if keyword.lower() in m.product_name.lower() or keyword.lower() in s_name.lower():
                data.append({
                    "date": str(m.date)[:10],
                    "movement_id": m.movement_id[:8],
                    "product": m.product_name,
                    "quantity": m.quantity,
                    "unit": m.unit,
                    "price": m.price,
                    "supplier": s_name
                })

        return ReportResult({"total": len(data)}, data)


    def report_sales(self):
        active = [i for i in self.invoice_controller.get_all() if i.is_active]
        data = [{
            "invoice_number": i.invoice_id[:8],
            "date": str(i.date)[:10],
            "client": i.customer,
            "product": i.product,
            "total_price": i.total_price,
            "status": "АКТИВНА" # Добавено изрично за Вюто
        } for i in active]

        return ReportResult({"total": len(active)}, data)


    def fifo_analysis_for_product(self, name_or_id):
        pid = self.inventory_controller._product_id(name_or_id)
        product = self.product_controller.get_by_id(pid)

        if not product:
            return None

        active_invoices = [
            i for i in self.invoice_controller.get_all()
            if i.is_active and i.product == product.name
        ]

        total_out = sum(float(i.quantity) for i in active_invoices)
        revenue = sum(float(i.total_price) for i in active_invoices)


        fifo_cost = self.inventory_controller.calculate_fifo_cost(
            pid,
            self.movement_controller.movements,
            product.price
        )

        return {
            "product": product.name,
            "unit": product.unit,
            "total_out": total_out,
            "revenue": round(revenue, 2),
            "fifo_cost": fifo_cost,
            "profit": round(revenue - fifo_cost, 2)
        }