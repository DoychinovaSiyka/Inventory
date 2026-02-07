from datetime import datetime
from models.report import Report


class ReportController:
    def __init__(self, repo, product_controller, movement_controller, invoice_controller):
        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.reports = [Report.from_dict(r) for r in self.repo.load()]


    # ID GENERATOR

    def _generate_id(self):
        if not self.reports:
            return 1
        return max(r.report_id for r in self.reports) + 1


    # INTERNAL SAVE

    def _save(self):
        self.repo.save([r.to_dict() for r in self.reports])


    # CREATE REPORT OBJECT
    def _create_report(self, report_type, parameters, data):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        report = Report(
            report_id=self._generate_id(),
            report_type=report_type,generated_on=now,parameters=parameters,data=data)

        self.reports.append(report)
        self._save()
        return report

    # 1. STOCK REPORT

    def report_stock(self):
        products = self.product_controller.products

        data = [
            {
                "product": p.name,
                "quantity": p.quantity,
                "price": p.price,
                "location": getattr(p, "location_id", None)
            }
            for p in products
        ]

        return self._create_report("stock", {}, data)


    # 2. ALL MOVEMENTS

    def report_movements(self):
        movements = self.movement_controller.movements

        data = [
            {
                "date": m.date,
                "type": m.movement_type.name,
                "product_id": m.product_id,
                "quantity": m.quantity,
                "price": m.price,
                "location": m.location_id
            }
            for m in movements
        ]

        return self._create_report("movements_all", {}, data)


    # 3. MOVEMENTS BY PRODUCT

    def report_movements_by_product(self, keyword):
        keyword = keyword.lower()

        data = []

        for m in self.movement_controller.movements:
            product = self.product_controller.get_by_id(m.product_id)

            # Ако продуктът е изтрит → пропускаме движението
            if not product:
                continue

            if keyword in product.name.lower():
                data.append({
                    "date": m.date,
                    "type": m.movement_type.name,
                    "quantity": m.quantity,
                    "price": m.price
                })

        return self._create_report("movements_by_product", {"keyword": keyword}, data)

    # 4. MOVEMENTS BY TYPE

    def report_movements_by_type(self, movement_type):
        movement_type = movement_type.upper()

        data = [
            {
                "date": m.date,
                "product_id": m.product_id,
                "quantity": m.quantity
            }
            for m in self.movement_controller.movements
            if m.movement_type.name == movement_type
        ]

        return self._create_report("movements_by_type", {"type": movement_type}, data)


    # 5. MOVEMENTS BY DATE

    def report_movements_by_date(self, date_str):
        data = [
            {
                "date": m.date,
                "type": m.movement_type.name,
                "quantity": m.quantity
            }
            for m in self.movement_controller.movements
            if m.date.startswith(date_str)
        ]

        return self._create_report("movements_by_date", {"date": date_str}, data)


    # 6. SALES REPORT

    def report_sales(self):
        invoices = self.invoice_controller.invoices

        data = [
            {
                "date": inv.date,
                "product": inv.product,
                "quantity": inv.quantity,
                "total_price": inv.total_price,
                "customer": inv.customer
            }
            for inv in invoices
        ]

        return self._create_report("sales_all", {}, data)


    # 7. SALES BY CUSTOMER

    def report_sales_by_customer(self, customer):
        invoices = self.invoice_controller.search_by_customer(customer)

        data = [
            {
                "date": inv.date,
                "product": inv.product,
                "quantity": inv.quantity,
                "total_price": inv.total_price
            }
            for inv in invoices
        ]

        return self._create_report("sales_by_customer", {"customer": customer}, data)


    # 8. SALES BY PRODUCT

    def report_sales_by_product(self, product):
        invoices = self.invoice_controller.search_by_product(product)

        data = [
            {
                "date": inv.date,
                "customer": inv.customer,
                "quantity": inv.quantity,
                "total_price": inv.total_price
            }
            for inv in invoices
        ]

        return self._create_report("sales_by_product", {"product": product}, data)


    # 9. SALES BY DATE

    def report_sales_by_date(self, date_str):
        invoices = self.invoice_controller.search_by_date(date_str)

        data = [
            {
                "product": inv.product,
                "quantity": inv.quantity,
                "total_price": inv.total_price,
                "customer": inv.customer
            }
            for inv in invoices
        ]

        return self._create_report("sales_by_date", {"date": date_str}, data)
