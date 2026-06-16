from models.movement import MovementType
from datetime import datetime
from models.report import Report
from filters import product_sorters




class ReportController:
    # Контролерът взима данни от другите контролери и ги комбинира, за да върне готов отчет за показване.
    def __init__(self, product_controller, movement_controller, invoice_controller,
                 location_controller, inventory_controller, supplier_controller):


        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller
        self.supplier_controller = supplier_controller



    # дали даден текст съдържа ключова дума
    def _match_string(self, target: str, keyword: str) -> bool:
        if not keyword:
            return True
        return keyword.lower().strip() in (target or "").lower()



    # Филтрираме движенията по тип – IN, OUT или MOVE
    def _filter_movements_by_type(self, movements, m_type: str):
        return [m for m in movements if m.movement_type.name == m_type.upper()]



    # Пълен инвентарен отчет
    def report_inventory_full(self):
        # Взимаме суровите данни от инвентара
        raw_inventory = self.inventory_controller.build_inventory()
        report_data = []

        for item in raw_inventory["products"]:
            pid = item["product_id"]

            # всички движения за този продукт
            moves = [m for m in self.movement_controller.movements if str(m.product_id) == pid]
            in_moves = [m for m in moves if m.movement_type.name == "IN"]
            out_moves = [m for m in moves if m.movement_type.name == "OUT"]

            # Колко е доставено и колко е продадено
            delivered = sum(float(m.quantity) for m in in_moves)
            sold = sum(float(m.quantity) for m in out_moves)

            in_prices = [float(m.price) for m in in_moves if m.price]
            out_prices = [float(m.price) for m in out_moves if m.price]

            avg_in = round(sum(in_prices) / len(in_prices), 2) if in_prices else 0.0
            avg_out = round(sum(out_prices) / len(out_prices), 2) if out_prices else 0.0


            report_item = {"product": item["product_name"], "unit": item["unit"], "total": item["total"],
                           "warehouses": item["warehouses"], "delivered": delivered, "sold": sold,
                           "avg_in_price": f"{avg_in:.2f} лв.", "avg_out_price": f"{avg_out:.2f} лв.",
                           "expense": f"{round(delivered * avg_in, 2):.2f} лв.",
                           "revenue": f"{round(sold * avg_out, 2):.2f} лв."}

            # Последно движение за продукта
            if moves:
                last = sorted(moves, key=lambda x: x.date)[-1]
                report_item["last_movement"] = f"{last.movement_type.name} - {str(last.date)[:19]}"
            else:
                report_item["last_movement"] = "Няма движения"

            report_data.append(report_item)


        return Report(report_type="Inventory Full", data=report_data)

    def report_movements(self):
        rows = []

        for m in self.movement_controller.movements:

            loc_from = self.location_controller.get_by_id(m.from_location_id) if m.from_location_id else None
            loc_to = self.location_controller.get_by_id(m.to_location_id) if m.to_location_id else None
            loc_main = self.location_controller.get_by_id(m.location_id)

            sup = self.supplier_controller.get_by_id(m.supplier_id) if m.supplier_id else None
            supplier_name = sup.name if sup else None

            client_name = m.customer if m.customer else None

            if m.movement_type.name == "IN":
                from_name = supplier_name or "Доставчик"
                to_name = loc_main.name if loc_main else "Склад"

            elif m.movement_type.name == "OUT":
                from_name = loc_main.name if loc_main else "Склад"
                to_name = client_name or "Клиент"

            else:  # MOVE
                from_name = loc_from.name if loc_from else "Склад"
                to_name = loc_to.name if loc_to else "Склад"

            rows.append({"date": str(m.date)[:10], "movement_id": m.movement_id[:8], "type": m.movement_type.name,
                         "product": m.product_name, "quantity": m.quantity, "unit": m.unit, "from": from_name, "to": to_name})

        return Report(report_type="Movement History", data=rows)



    # Отчет за всички доставки
    def report_deliveries_all(self, keyword=""):
        moves = self._filter_movements_by_type(self.movement_controller.movements, "IN")
        data = []

        for m in moves:
            sup = self.supplier_controller.get_by_id(m.supplier_id)
            supplier_name = sup.name if sup else "Неизвестен"

            # Филтър по продукт или доставчик
            if self._match_string(m.product_name, keyword) or self._match_string(supplier_name, keyword):
                data.append({"date": str(m.date)[:10], "movement_id": m.movement_id[:8],
                             "product": m.product_name, "quantity": m.quantity, "unit": m.unit,
                             "price": m.price, "supplier": supplier_name})
        return Report(report_type="Deliveries", data=data)



    # Отчет за продажбите – активните фактури
    def report_sales(self):
        active = [i for i in self.invoice_controller.get_all() if i.is_active]
        data = [{"invoice_number": i.invoice_id[:8], "date": str(i.date)[:10], "client": i.customer,
                 "product": i.product, "total_price": i.total_price, "status": "АКТИВНА"} for i in active]

        return Report(report_type="Sales", data=data)

    def sort_inventory_by_quantity(self, algorithm="merge", reverse=True):
        data = self.report_inventory_full().data[:]
        key_fn = lambda x: x["total"]

        if algorithm == "merge":
            sorted_data = product_sorters.merge_sort(data, key=key_fn, reverse=reverse)
        elif algorithm == "quick":
            sorted_data = product_sorters.quick_sort(data, key=key_fn, reverse=reverse)
        else:
            raise ValueError(f"Unknown sorting algorithm: {algorithm}")

        return Report(report_type=f"Sort by Quantity ({algorithm})", data=sorted_data)






    def filter_movements(self, type=None, product=None, supplier=None, client=None, warehouse=None, date_from=None, date_to=None):

        movements = self.movement_controller.movements
        filtered = []

        for m in movements:
            if type and m.movement_type.name != type.upper():
                continue


            if product and product.lower() not in m.product_name.lower():
                continue


            sup = self.supplier_controller.get_by_id(m.supplier_id) if m.supplier_id else None
            supplier_name = sup.name if sup else None


            if supplier:
                if not supplier_name or supplier.lower() not in supplier_name.lower():
                    continue

            client_name = m.customer if m.customer else None
            if client:
                if not client_name or client.lower() not in client_name.lower():
                    continue

            if warehouse:
                w = warehouse.lower()
                match_found = False

                loc_ids = [m.location_id, m.from_location_id, m.to_location_id]

                for lid in loc_ids:
                    if not lid:
                        continue

                    loc = self.location_controller.get_by_id(lid)
                    if not loc:
                        continue

                    if w == loc.name.lower() or w == str(loc.location_id).lower():
                        match_found = True
                        break

                if not match_found:
                    continue



            m_date = str(m.date)[:10]
            if date_from and m_date < date_from:
                continue
            if date_to and m_date > date_to:
                continue


            if m.movement_type.name == "IN":
                loc_main = self.location_controller.get_by_id(m.location_id)
                loc_name = loc_main.name if loc_main else "Склад"

                from_name = supplier_name or "Доставчик"
                to_name = loc_name

            elif m.movement_type.name == "OUT":
                loc_main = self.location_controller.get_by_id(m.location_id)
                loc_name = loc_main.name if loc_main else "Склад"

                from_name = loc_name
                to_name = client_name or "Клиент"

            else:
                loc_from = self.location_controller.get_by_id(m.from_location_id) if m.from_location_id else None
                loc_to = self.location_controller.get_by_id(m.to_location_id) if m.to_location_id else None

                from_name = loc_from.name if loc_from else "Склад"
                to_name = loc_to.name if loc_to else "Склад"

            filtered.append({"date": m_date, "movement_id": m.movement_id[:8], "type": m.movement_type.name,
                             "product": m.product_name, "quantity": m.quantity,
                             "unit": m.unit, "from": from_name, "to": to_name})

        return Report(report_type="Filtered Movements", data=filtered)
