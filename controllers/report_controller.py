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
        mapped = []

        for i in invoices:
            row = {"invoice_number": i.invoice_id[:8], "date": i.date[:10], "client": i.customer,
                   "product": i.product, "total_price": i.total_price}
            mapped.append(row)

        return mapped


    # Продажби
    def report_sales(self):
        invoices = self.invoice_controller.get_all()

        if not invoices:
            invoices = []

        total_sum = 0.0
        for i in invoices:
            try:
                total_sum += float(i.total_price)
            except Exception:
                total_sum += 0.0

        summary = {"total_count": len(invoices), "total_revenue": round(total_sum, 2)}

        data = self._map_invoices_to_data(invoices)
        return ReportResult(summary, data)

    def report_sales_by_customer(self, customer_name: str):
        all_movements = self.movement_controller.get_all()

        if isinstance(all_movements, dict):
            temp = []
            for key in all_movements:
                temp.append(all_movements[key])
            all_movements = temp

        result = []
        search_name = customer_name.lower()

        for m in all_movements:
            if m.movement_type.name == "OUT":
                if m.customer is not None:
                    current_customer = m.customer.lower()
                else:
                    current_customer = ""

                if search_name in current_customer:
                    result.append(m)

        return result

    def report_sales_by_product(self, product_name: str):
        all_movements = self.movement_controller.get_all()

        if isinstance(all_movements, dict):
            temp = []
            for key in all_movements:
                temp.append(all_movements[key])
            all_movements = temp

        result = []
        search_name = product_name.lower()

        for m in all_movements:
            if m.movement_type.name == "OUT":
                product_obj = self.product_controller.get_by_id(m.product_id)

                if product_obj is not None:
                    current_product_name = product_obj.name.lower()
                else:
                    current_product_name = ""

                if search_name in current_product_name:
                    result.append(m)

        return result


    # Движения
    def report_movements(self):
        data = []

        for m in self.movement_controller.movements:
            mtype = m.movement_type.name

            # FROM / TO локации
            if mtype == "IN":
                f_loc = "Доставчик"

                t_loc_obj = self.location_controller.get_by_id(m.location_id)
                if t_loc_obj:
                    t_loc = t_loc_obj.name
                else:
                    t_loc = "Склад"

            elif mtype == "OUT":
                f_loc_obj = self.location_controller.get_by_id(m.location_id)
                if f_loc_obj:
                    f_loc = f_loc_obj.name
                else:
                    f_loc = "Склад"

                if m.customer:
                    t_loc = m.customer
                else:
                    t_loc = "Клиент"

            elif mtype == "MOVE":
                fl_obj = self.location_controller.get_by_id(m.from_location_id)
                if fl_obj:
                    f_loc = fl_obj.name
                else:
                    f_loc = "Източник"

                tl_obj = self.location_controller.get_by_id(m.to_location_id)
                if tl_obj:
                    t_loc = tl_obj.name
                else:
                    t_loc = "Цел"

            else:
                f_loc = "Няма"
                t_loc = "Няма"

            movement_id_short = m.movement_id[:8]
            date_short = str(m.date)[:10]
            product_name = m.product_name
            quantity = m.quantity
            unit = m.unit

            row = {"movement_id": movement_id_short, "date": date_short, "type": mtype,
                   "product": product_name, "quantity": quantity, "unit": unit, "from": f_loc,
                   "to": t_loc}

            data.append(row)

        summary = {"total": len(data)}
        return ReportResult(summary, data)


    # Доставки
    def report_deliveries_all(self, keyword=None):
        data = []

        for m in self.movement_controller.movements:
            if m.movement_type.name != "IN":
                continue

            p_name = m.product_name

            sup_obj = None
            if m.supplier_id:
                sup_obj = self.supplier_controller.get_by_id(m.supplier_id)

            if sup_obj:
                supplier_name = sup_obj.name
            else:
                supplier_name = "Неизвестен"

            if keyword:
                kw = keyword.lower()
                if kw not in p_name.lower() and kw not in supplier_name.lower():
                    continue

            price_value = 0.0
            if m.price is not None:
                try:
                    price_value = float(m.price)
                except Exception:
                    price_value = 0.0

            row = {"movement_id": m.movement_id[:8], "date": str(m.date)[:10], "product": p_name,
                   "quantity": m.quantity, "unit": m.unit, "price": price_value,
                   "supplier": supplier_name}

            data.append(row)

        summary = {"total": len(data)}
        return ReportResult(summary, data)


    # Обобщена наличност
    def report_inventory_summary(self):
        data = []

        for p in self.product_controller.get_all():
            pid = str(p.product_id)
            stock = self.inventory_controller.get_total_stock(pid)

            sold = 0.0
            for m in self.movement_controller.movements:
                if str(m.product_id) == pid and m.movement_type.name == "OUT":
                    try:
                        sold += float(m.quantity)
                    except Exception:
                        sold += 0.0

            if sold > 0:
                sold_text = str(sold) + " " + p.unit
            else:
                sold_text = "0"

            row = {"product": p.name, "available": str(stock) + " " + p.unit,
                   "sold": sold_text, "top_locations": "Виж Инвентар"}

            data.append(row)

        summary = {"total": len(data)}
        return ReportResult(summary, data)


    # Финансов живот на продукт
    def product_lifecycle(self, name_or_id):
        product = self.product_controller.get_by_id(name_or_id)

        if not product:
            for p in self.product_controller.get_all():
                if name_or_id.lower() in p.name.lower():
                    product = p
                    break

        if not product:
            return None

        pid = str(product.product_id)
        movements = self.movement_controller.movements

        prod_moves = []
        for m in movements:
            if str(m.product_id) == pid:
                prod_moves.append(m)

        total_in = 0.0
        total_out = 0.0

        for m in prod_moves:
            if m.movement_type.name == "IN":
                total_in += float(m.quantity)
            elif m.movement_type.name == "OUT":
                total_out += float(m.quantity)

        revenue = 0.0
        for m in prod_moves:
            if m.movement_type.name == "OUT":
                try:
                    revenue += float(m.quantity) * float(m.price)
                except Exception:
                    revenue += 0.0

        fifo_cost = self.inventory_controller.calculate_fifo_cost(pid, movements, product.price)

        result = {"product": product.name, "unit": product.unit, "total_in": total_in,
                  "total_out": total_out,
                  "current_stock": self.inventory_controller.get_total_stock(pid),
                  "revenue": round(revenue, 2), "fifo_cost": round(fifo_cost, 2),
                  "profit": round(revenue - fifo_cost, 2)}

        return result
