from models.movement import MovementType


class ReportResult:
    def __init__(self, data):
        self.data = data


class ReportController:
    """
    Чист MVC контролер:
    - НЕ пази състояние
    - НЕ модифицира модели
    - НЕ прави бизнес логика
    - Само събира данни от други контролери
    - Връща ги към View
    """

    def __init__(self, repo, product_controller, movement_controller,
                 invoice_controller, location_controller, inventory_controller):

        self.repo = repo
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.location_controller = location_controller
        self.inventory_controller = inventory_controller

    # СПРАВКА: ВСИЧКИ ДВИЖЕНИЯ
    def report_movements(self):
        data = []

        for m in self.movement_controller.movements:
            product = self.product_controller.get_by_id(m.product_id)
            if product:
                product_name = product.name
            else:
                product_name = "Неизвестен продукт"

            location = self.location_controller.get_by_id(m.location_id)
            if location:
                location_name = location.name
            else:
                location_name = "N/A"

            data.append({
                "movement_id": m.movement_id,
                "product_name": product_name,
                "type": m.movement_type.name,
                "quantity": m.quantity,
                "unit": m.unit,
                "price": m.price,
                "location_name": location_name,
                "date": m.date
            })

        return ReportResult(data)

    # СПРАВКА: ВСИЧКИ ПРОДАЖБИ
    def report_sales(self):
        invoices = self.invoice_controller.get_all()
        if invoices is None:
            invoices = []

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

    # СПРАВКА: ПРОДАЖБИ ПО КЛИЕНТ
    def report_sales_by_customer(self, customer):
        customer = customer.lower()
        invoices = self.invoice_controller.get_all()
        if invoices is None:
            invoices = []

        data = []

        for inv in invoices:
            if inv.customer is not None and customer in inv.customer.lower():
                data.append({
                    "invoice_number": inv.invoice_id,
                    "date": inv.date,
                    "client": inv.customer,
                    "product": inv.product,
                    "total_price": inv.total_price
                })

        return ReportResult(data)

    # СПРАВКА: ПРОДАЖБИ ПО ПРОДУКТ
    def report_sales_by_product(self, product):
        product = product.lower()
        invoices = self.invoice_controller.get_all()
        if invoices is None:
            invoices = []

        data = []

        for inv in invoices:
            if inv.product is not None and product in inv.product.lower():
                data.append({
                    "invoice_number": inv.invoice_id,
                    "date": inv.date,
                    "client": inv.customer,
                    "product": inv.product,
                    "total_price": inv.total_price
                })

        return ReportResult(data)

    # СПРАВКА: ПРОДАЖБИ ПО ДАТА
    def report_sales_by_date(self, date):
        invoices = self.invoice_controller.get_all()
        if invoices is None:
            invoices = []

        data = []

        for inv in invoices:
            if inv.date is not None and date in inv.date:
                data.append({
                    "invoice_number": inv.invoice_id,
                    "date": inv.date,
                    "client": inv.customer,
                    "product": inv.product,
                    "total_price": inv.total_price
                })

        return ReportResult(data)

    # СПРАВКА: ВСИЧКИ ДОСТАВКИ (IN)
    def report_deliveries_all(self):
        data = []

        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.IN:
                continue

            product = self.product_controller.get_by_id(m.product_id)
            if product:
                product_name = product.name
            else:
                product_name = "Неизвестен продукт"

            location = self.location_controller.get_by_id(m.location_id)
            if location:
                location_name = location.name
            else:
                location_name = "N/A"

            supplier_name = "N/A"
            if self.movement_controller.supplier_controller is not None:
                supplier = self.movement_controller.supplier_controller.get_by_id(m.supplier_id)
                if supplier:
                    supplier_name = supplier.name

            data.append({
                "date": m.date,
                "movement_id": m.movement_id,
                "product": product_name,
                "quantity": m.quantity,
                "unit": m.unit,
                "supplier": supplier_name,
                "location_name": location_name
            })

        return ReportResult(data)

    # СПРАВКА: ОБОРОТ ПО ДНИ
    def report_turnover_by_day(self):
        invoices = self.invoice_controller.get_all()
        if invoices is None:
            invoices = []

        daily = {}

        for inv in invoices:
            if inv.date is not None:
                day = inv.date[:10]
            else:
                day = "N/A"

            if day not in daily:
                daily[day] = {"count": 0, "total": 0.0}

            daily[day]["count"] += 1
            daily[day]["total"] += inv.total_price

        data = []

        for d, v in daily.items():
            data.append({
                "date": d,
                "count": v["count"],
                "total": v["total"]
            })

        return ReportResult(data)

    # СПРАВКА: НАЙ-ПРОДАВАНИ ПРОДУКТИ
    def report_top_products(self):
        stats = {}

        for m in self.movement_controller.movements:
            if m.movement_type != MovementType.OUT:
                continue

            product = self.product_controller.get_by_id(m.product_id)
            if product is None:
                continue

            name = product.name

            if name not in stats:
                stats[name] = {"quantity": 0, "total": 0.0, "unit": product.unit}

            stats[name]["quantity"] += m.quantity
            stats[name]["total"] += m.quantity * m.price

        data = []

        for name, info in stats.items():
            data.append({
                "product": name,
                "quantity": info["quantity"],
                "total": info["total"],
                "unit": info["unit"]
            })

        data.sort(key=lambda x: x["quantity"], reverse=True)
        return ReportResult(data)

    # СПРАВКА: ОБОБЩЕНА НАЛИЧНОСТ
    def report_inventory_summary(self):
        data = []

        if self.inventory_controller is None:
            return ReportResult([])

        inv_data = self.inventory_controller.data
        if inv_data is None:
            inv_data = {}

        products_data = inv_data.get("products", {})

        for product in self.product_controller.get_all():
            pid = product.product_id
            unit = product.unit

            if self.inventory_controller:
                current_stock = self.inventory_controller.get_total_stock(pid)
            else:
                current_stock = 0.0

            sold = 0.0
            for m in self.movement_controller.movements:
                if m.product_id == pid and m.movement_type == MovementType.OUT:
                    sold += m.quantity

            if pid in products_data:
                locations = products_data[pid].get("locations", {})
            else:
                locations = {}

            sorted_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)
            top3 = sorted_locations[:3]

            if len(top3) > 0:
                top3_str = ", ".join([f"{loc}:{qty}" for loc, qty in top3])
            else:
                top3_str = "-"

            data.append({
                "product": product.name,
                "available": f"{current_stock} {unit}",
                "sold": f"{sold} {unit}" if sold > 0 else "-",
                "top_locations": top3_str
            })

        return ReportResult(data)

    # СПРАВКА: ЖИЗНЕН ЦИКЪЛ НА ПРОДУКТ
    def product_lifecycle(self, name):
        name = name.lower()

        product = None
        for p in self.product_controller.get_all():
            if name in p.name.lower():
                product = p
                break

        if product is None:
            return None

        pid = product.product_id
        unit = product.unit

        if self.inventory_controller:
            current_stock = self.inventory_controller.get_total_stock(pid)
        else:
            current_stock = 0.0

        total_in = 0.0
        total_out = 0.0
        first_in = None

        for m in self.movement_controller.movements:
            if m.product_id != pid:
                continue

            if m.movement_type == MovementType.IN:
                total_in += m.quantity
                if first_in is None:
                    first_in = m.quantity

            elif m.movement_type == MovementType.OUT:
                total_out += m.quantity

        if first_in is None:
            initial_stock = 0.0
        else:
            initial_stock = first_in

        return {
            "product": product.name,
            "unit": unit,
            "initial_stock": initial_stock,
            "total_in": total_in,
            "total_out": total_out,
            "expected_stock": current_stock,
            "current_stock": current_stock,
            "revenue": total_out * product.price
        }
