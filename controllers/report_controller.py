from typing import List, Dict
from models.movement import MovementType


class ReportResult:
    def __init__(self, data):
        self.data = data


class ReportController:
    def __init__(self, repo, product_controller, movement_controller,
                 invoice_controller, location_controller, inventory_controller):

        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller


    #  Справка за движения
    def report_movements(self):
        data = []
        for m in self.movement_controller.movements:

            product = self.product_controller.get_by_id(m.product_id)
            product_name = product.name if product else "Неизвестен продукт"

            location = self.location_controller.get_by_id(m.location_id)

            data.append({
                "movement_id": m.movement_id,
                "product_name": product_name,
                "type": m.movement_type.name,
                "quantity": m.quantity,
                "unit": m.unit,
                "price": m.price,
                "location_name": location.name if location else "N/A",
                "date": m.date
            })
        return ReportResult(data)


    #  Всички продажби (фактури)
    def report_sales(self):
        invoices = self.invoice_controller.get_all()
        data = []

        for inv in invoices:
            data.append({
                "invoice_number": inv.invoice_id,
                "date": inv.date,
                "client": inv.customer,
                "product": inv.product,
                "total_price": inv.total_price
            })

        return ReportResult(data)


    #  Търсене по клиент
    def report_sales_by_customer(self, customer: str):
        customer = customer.lower()
        invoices = self.invoice_controller.get_all()

        data = [
            {
                "invoice_number": i.invoice_id,
                "date": i.date,
                "client": i.customer,
                "product": i.product,
                "total_price": i.total_price
            }
            for i in invoices
            if customer in i.customer.lower()
        ]

        return ReportResult(data)



    def report_sales_by_product(self, product: str):
        product = product.lower()
        invoices = self.invoice_controller.get_all()

        data = [
            {
                "invoice_number": i.invoice_id,
                "date": i.date,
                "client": i.customer,
                "product": i.product,
                "total_price": i.total_price
            }
            for i in invoices
            if product in i.product.lower()
        ]

        return ReportResult(data)


    #  Търсене по дата
    def report_sales_by_date(self, date: str):
        invoices = self.invoice_controller.get_all()

        data = [
            {
                "invoice_number": i.invoice_id,
                "date": i.date,
                "client": i.customer,
                "product": i.product,
                "total_price": i.total_price
            }
            for i in invoices
            if date in i.date
        ]

        return ReportResult(data)


    #  Доставки
    def report_deliveries_all(self):
        data = []
        for m in self.movement_controller.movements:
            if m.movement_type == MovementType.IN:

                product = self.product_controller.get_by_id(m.product_id)
                product_name = product.name if product else "Неизвестен продукт"

                location = self.location_controller.get_by_id(m.location_id)
                supplier = None
                if m.supplier_id:
                    supplier = self.movement_controller.supplier_controller.get_by_id(m.supplier_id)

                data.append({
                    "date": m.date,
                    "movement_id": m.movement_id,
                    "product": product_name,
                    "quantity": m.quantity,
                    "unit": m.unit,
                    "supplier": supplier.name if supplier else "N/A",
                    "location_name": location.name if location else "N/A"
                })
        return ReportResult(data)

    def search_deliveries_all(self, keyword: str):
        keyword = keyword.lower()
        res = self.report_deliveries_all()
        filtered = [d for d in res.data if keyword in str(d).lower()]
        return ReportResult(filtered)


    #  Оборот по дни
    def report_turnover_by_day(self):
        invoices = self.invoice_controller.get_all()
        daily = {}

        for inv in invoices:
            day = inv.date[:10]
            if day not in daily:
                daily[day] = {"count": 0, "total": 0.0}
            daily[day]["count"] += 1
            daily[day]["total"] += inv.total_price

        data = [{"date": d, "count": v["count"], "total": v["total"]} for d, v in daily.items()]
        return ReportResult(data)


    #  Най-продавани продукти —  (ползва OUT движения)
    def report_top_products(self):
        stats = {}

        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.OUT:
                continue

            product = self.product_controller.get_by_id(m.product_id)
            if not product:
                continue

            name = product.name

            if name not in stats:
                stats[name] = {"quantity": 0, "total": 0.0, "unit": product.unit}

            stats[name]["quantity"] += m.quantity
            stats[name]["total"] += m.quantity * m.price

        data = [
            {"product": k, "quantity": v["quantity"], "total": v["total"], "unit": v["unit"]}
            for k, v in stats.items()
        ]

        data.sort(key=lambda x: x["quantity"], reverse=True)
        return ReportResult(data)



    #  ОБОБЩЕНА СПРАВКА ЗА НАЛИЧНОСТИ (Избор: 1)
    def report_inventory_summary(self):
        data = []

        for product in self.product_controller.get_all():
            pid = product.product_id
            name = product.name
            unit = product.unit

            # Текуща наличност от инвентара
            current_stock = self.inventory_controller.get_total_stock(pid)

            # Продадено количество (OUT)
            sold = 0.0
            for m in self.movement_controller.movements:
                if m.product_id == pid and m.movement_type == MovementType.OUT:
                    sold += m.quantity

            # Топ 3 склада
            locations = self.inventory_controller.data["products"].get(pid, {}).get("locations", {})
            top3 = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:3]
            top3_str = ", ".join([f"{loc}:{qty}" for loc, qty in top3]) if top3 else "-"

            data.append({
                "product": name,
                "available": f"{current_stock} {unit}",
                "sold": f"{sold} {unit}" if sold > 0 else "-",
                "top_locations": top3_str
            })

        return ReportResult(data)


    def product_lifecycle(self, name: str):
        name = name.lower()

        product = None
        for p in self.product_controller.get_all():
            if name in p.name.lower():
                product = p
                break

        if not product:
            return None

        current_stock = self.inventory_controller.get_total_stock(product.product_id)

        total_in = 0.0
        total_out = 0.0

        for m in self.movement_controller.movements:
            if m.product_id != product.product_id:
                continue

            if m.movement_type == MovementType.IN:
                total_in += m.quantity
            elif m.movement_type == MovementType.OUT:
                total_out += m.quantity

        initial_stock = current_stock - total_in + total_out

        return {
            "product": product.name,
            "unit": product.unit,
            "initial_stock": initial_stock,
            "total_in": total_in,
            "total_out": total_out,
            "expected_stock": current_stock,
            "current_stock": current_stock,
            "revenue": total_out * product.price
        }
