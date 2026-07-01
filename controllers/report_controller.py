from models.movement import MovementType
from datetime import datetime
from models.report import Report
from storage.json_repository import JSONRepository


class ReportController:
    """Чист MVC контролер за отчети."""

    def __init__(self, inventory_controller, movement_controller, supplier_controller, location_controller, invoice_controller):
        self.inventory_controller = inventory_controller
        self.movement_controller = movement_controller
        self.supplier_controller = supplier_controller
        self.location_controller = location_controller
        self.invoice_controller = invoice_controller

        self.report_repo = JSONRepository("data/reports.json")
        self.inventory_repo = JSONRepository("data/inventory.json")

    # -----------------------------
    # SAVE REPORT HISTORY
    # -----------------------------
    def save_report(self, report: Report):
        existing = self.report_repo.load() or []
        existing.append(report.to_dict())
        self.report_repo.save(existing)

    # -----------------------------
    # SAVE INVENTORY LIST REPORT
    # -----------------------------
    def save_inventory_list_report(self):
        report = self.report_inventory_full()

        final = {
            "products": report.data,
            "summary": {
                "total_products": len(report.data)
            },
            "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        self.inventory_repo.save(final)

    # -----------------------------
    # MOVEMENTS REPORT (with warehouse names)
    # -----------------------------
    def report_movements(self):
        movements = self.movement_controller.get_all()
        data = []

        for m in movements:

            # FROM warehouse name
            if m.from_location_id:
                loc_from = self.location_controller.get_by_id(m.from_location_id)
                from_name = loc_from.name if loc_from else "-"
            else:
                from_name = "-"

            # TO warehouse name
            if m.to_location_id:
                loc_to = self.location_controller.get_by_id(m.to_location_id)
                to_name = loc_to.name if loc_to else "-"
            else:
                to_name = "-"

            data.append({
                "date": str(m.date)[:19],
                "movement_id": m.movement_id,
                "type": m.movement_type.name,
                "product": m.product_name,
                "quantity": m.quantity,
                "unit": m.unit,
                "from": from_name,
                "to": to_name
            })

        data = sorted(data, key=lambda x: x["date"])
        return Report(report_type="Movements", data=data)

    # -----------------------------
    # DELIVERIES REPORT (IN)
    # -----------------------------
    def report_deliveries_all(self, _filter=""):
        movements = self.movement_controller.get_all()
        deliveries = [m for m in movements if m.movement_type == MovementType.IN]

        data = []
        for m in deliveries:
            supplier = self.supplier_controller.get_by_id(m.supplier_id)
            supplier_name = supplier.name if supplier else "Неизвестен доставчик"

            data.append({
                "date": str(m.date)[:19],
                "movement_id": m.movement_id,
                "product": m.product_name,
                "quantity": m.quantity,
                "unit": m.unit,
                "price": m.price,
                "supplier": supplier_name
            })

        data = sorted(data, key=lambda x: x["date"])
        return Report(report_type="Deliveries", data=data)

    # -----------------------------
    # SALES REPORT (OUT)
    # -----------------------------
    def report_sales(self):
        invoices = self.invoice_controller.get_all()
        data = []

        for inv in invoices:
            data.append({
                "invoice_number": inv.invoice_id,
                "date": str(inv.date)[:19],
                "client": inv.customer,
                "product": inv.product,
                "total_price": inv.total_price,
                "status": "ВАЛИДНА" if inv.is_active else "АНУЛИРАНА"
            })

        data = sorted(data, key=lambda x: x["date"])
        return Report(report_type="Sales", data=data)

    # -----------------------------
    # SORT INVENTORY BY QUANTITY
    # -----------------------------
    def sort_inventory_by_quantity(self, algorithm="merge", reverse=False):
        inventory_data = self.inventory_controller.build_inventory()
        items = list(inventory_data["products"].values())

        sorted_items = sorted(items, key=lambda x: float(x["total"]), reverse=reverse)
        return Report(report_type="Sorted Inventory", data=sorted_items)

    # -----------------------------
    # INVENTORY FULL REPORT
    # -----------------------------
    def report_inventory_full(self):
        inventory_data = self.inventory_controller.build_inventory()
        movements = self.movement_controller.get_all()

        report_data = []

        for pid, item in inventory_data["products"].items():

            moves = [m for m in movements if str(m.product_id) == pid]
            in_moves = [m for m in moves if m.movement_type.name == "IN"]
            out_moves = [m for m in moves if m.movement_type.name == "OUT"]

            delivered = sum(float(m.quantity) for m in in_moves)
            sold = sum(float(m.quantity) for m in out_moves)

            in_prices = [float(m.price) for m in in_moves if m.price]
            out_prices = [float(m.price) for m in out_moves if m.price]

            avg_in = round(sum(in_prices) / len(in_prices), 2) if in_prices else 0.0
            avg_out = round(sum(out_prices) / len(out_prices), 2) if out_prices else 0.0

            warehouse_names = {}
            for wid, qty in item["warehouses"].items():
                loc = self.location_controller.get_by_id(wid)
                warehouse_names[loc.name if loc else wid] = qty

            report_item = {
                "product_id": pid,
                "product_name": item["product_name"],
                "unit": item["unit"],
                "total": item["total"],
                "warehouses": warehouse_names,
                "delivered": delivered,
                "sold": sold,
                "avg_in_price": avg_in,
                "avg_out_price": avg_out,
                "expense": round(delivered * avg_in, 2),
                "revenue": round(sold * avg_out, 2)
            }

            if moves:
                last = sorted(moves, key=lambda x: x.date)[-1]
                report_item["last_movement"] = f"{last.movement_type.name} - {str(last.date)[:19]}"
            else:
                report_item["last_movement"] = "Няма движения"

            report_data.append(report_item)

        return Report(report_type="Inventory Full", data=report_data)

    # -----------------------------
    # FILTER MOVEMENTS (with warehouse names)
    # -----------------------------
    def filter_movements(self, type=None, product=None, supplier=None,
                         client=None, warehouse=None, date_from=None, date_to=None):

        movements = self.movement_controller.get_all()
        result = []

        for m in movements:
            ok = True

            # Тип
            if type and m.movement_type.name.upper() != type.upper():
                ok = False

            # Продукт
            if product and product.lower() not in m.product_name.lower():
                ok = False

            # Доставчик
            if supplier:
                if m.supplier_id:
                    sup = self.supplier_controller.get_by_id(m.supplier_id)
                    if not sup or supplier.lower() not in sup.name.lower():
                        ok = False
                else:
                    ok = False

            # Клиент
            if client:
                inv = self.invoice_controller.get_by_movement_id(m.movement_id)
                if not inv or client.lower() not in inv.customer.lower():
                    ok = False

            # FROM warehouse name
            if m.from_location_id:
                loc_from = self.location_controller.get_by_id(m.from_location_id)
                from_name = loc_from.name if loc_from else "-"
            else:
                from_name = "-"

            # TO warehouse name
            if m.to_location_id:
                loc_to = self.location_controller.get_by_id(m.to_location_id)
                to_name = loc_to.name if loc_to else "-"
            else:
                to_name = "-"

            # Склад филтър
            if warehouse:
                if warehouse.lower() not in from_name.lower() and warehouse.lower() not in to_name.lower():
                    ok = False

            # Дата
            if date_from and str(m.date)[:10] < date_from:
                ok = False
            if date_to and str(m.date)[:10] > date_to:
                ok = False

            if ok:
                result.append({
                    "date": str(m.date)[:19],
                    "movement_id": m.movement_id,
                    "type": m.movement_type.name,
                    "product": m.product_name,
                    "quantity": m.quantity,
                    "unit": m.unit,
                    "from": from_name,
                    "to": to_name
                })

        return Report(report_type="Filtered Movements", data=result)
