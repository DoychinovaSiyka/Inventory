from models.movement import MovementType
from models.report import Report
from datetime import datetime


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

    def _map_invoices_to_data(self, invoices):
        return [{"invoice_number": i.invoice_id[:8], "date": i.date[:10], "client": i.customer,
                 "product": i.product, "total_price": i.total_price} for i in invoices]

    def report_sales(self):
        invoices = self.invoice_controller.get_all() or []
        total_sum = sum(float(i.total_price) for i in invoices)
        return ReportResult({"total_count": len(invoices), "total_revenue": round(total_sum, 2)},
                            self._map_invoices_to_data(invoices))

    def report_movements(self):
        """Показва движението между реални локации. """
        data = []
        for m in self.movement_controller.movements:
            mtype = m.movement_type.name

            # Логика за локациите
            if mtype == "IN":
                f_loc = "Доставчик"
                t_loc_obj = self.location_controller.get_by_id(m.location_id)
                t_loc = t_loc_obj.name if t_loc_obj else "Склад"
            elif mtype == "OUT":
                f_loc_obj = self.location_controller.get_by_id(m.location_id)
                f_loc = f_loc_obj.name if f_loc_obj else "Склад"
                t_loc = (m.customer or "Клиент")
            elif mtype == "MOVE":
                fl_obj = self.location_controller.get_by_id(m.from_location_id)
                tl_obj = self.location_controller.get_by_id(m.to_location_id)
                f_loc = fl_obj.name if fl_obj else "Източник"
                t_loc = tl_obj.name if tl_obj else "Цел"
            else:
                f_loc, t_loc = "Н/А", "Н/А"

            data.append({ "movement_id": m.movement_id[:8], "date": str(m.date)[:10], "type": mtype,
                          "product": m.product_name,
                          "quantity": m.quantity, "unit": m.unit, "from": f_loc, "to": t_loc})

        return ReportResult({"total": len(data)}, data)


    def report_deliveries_all(self, keyword=None):
        data = []
        for m in self.movement_controller.movements:
            if m.movement_type.name != "IN": continue

            p_name = m.product_name
            sup_obj = self.supplier_controller.get_by_id(m.supplier_id)
            sup = sup_obj.name if (m.supplier_id and sup_obj) else "Неизвестен"

            if keyword and keyword.lower() not in p_name.lower() and keyword.lower() not in sup.lower():
                continue

            data.append({"movement_id": m.movement_id[:8], "date": str(m.date)[:10], "product": p_name,
                         "quantity": m.quantity, "unit": m.unit, "price": float(m.price or 0), "supplier": sup})
        return ReportResult({"total": len(data)}, data)

    def report_inventory_summary(self):
        data = []
        for p in self.product_controller.get_all():
            pid = str(p.product_id)
            stock = self.inventory_controller.get_total_stock(pid)

            # Филтрираме коректно OUT движенията за конкретния продукт
            sold = sum(float(m.quantity) for m in self.movement_controller.movements
                       if str(m.product_id) == pid and m.movement_type.name == "OUT")

            data.append({"product": p.name, "available": f"{stock} {p.unit}", "sold": f"{sold} {p.unit}"
            if sold > 0 else "0", "top_locations": "Виж Инвентар"})
        return ReportResult({"total": len(data)}, data)

    def product_lifecycle(self, name_or_id):
        """ Пълна финансова история на продукт. """
        product = self.product_controller.get_by_id(name_or_id)
        if not product:
            # Търсим продукт по част от името
            for p in self.product_controller.get_all():
                if name_or_id.lower() in p.name.lower():
                    product = p
                    break


        if not product:
            return None

        pid = str(product.product_id)
        movements = self.movement_controller.movements

        # Филтрираме движенията за този продукт веднъж
        prod_moves = [m for m in movements if str(m.product_id) == pid]

        total_in = sum(float(m.quantity) for m in prod_moves if m.movement_type.name == "IN")
        total_out = sum(float(m.quantity) for m in prod_moves if m.movement_type.name == "OUT")

        # ПРИХОДИ: Само от OUT движения
        revenue = sum(float(m.quantity) * float(m.price or 0) for m in prod_moves
                      if m.movement_type.name == "OUT")

        # FIFO Себестойност
        fifo_cost = self.inventory_controller.calculate_fifo_cost(pid, movements, product.price)

        return {"product": product.name, "unit": product.unit, "total_in": total_in, "total_out": total_out,
                "current_stock": self.inventory_controller.get_total_stock(pid), "revenue": round(revenue, 2),
                "fifo_cost": round(fifo_cost, 2), "profit": round(revenue - fifo_cost, 2)}