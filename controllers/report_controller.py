from datetime import datetime


class ReportController:
    def __init__(self, product_controller, movement_controller, invoice_controller, category_controller=None):
        self.product_controller = product_controller
        self.movement_controller = movement_controller
        self.invoice_controller = invoice_controller
        self.category_controller = category_controller

    # ---------------------------------------------------------
    # 1. Справка за наличности
    # ---------------------------------------------------------
    def report_stock(self):
        products = self.product_controller.get_all()

        print("\n=== Справка за наличности ===")
        if not products:
            print("Няма продукти.")
            return

        for p in products:
            print(f"- {p.name} | Количество: {p.quantity} | Цена: {p.price} | Локация: {p.location_id}")

    # ---------------------------------------------------------
    # 2. Справка за всички движения
    # ---------------------------------------------------------
    def report_movements(self):
        movements = self.movement_controller.get_all()

        print("\n=== Справка за движения ===")
        if not movements:
            print("Няма движения.")
            return

        for m in movements:
            print(f"{m.date} | {m.movement_type.name} | Продукт ID: {m.product_id} | "
                  f"Количество: {m.quantity} | Цена: {m.price} | Локация: {m.location_id}")

    # ---------------------------------------------------------
    # 3. Движения по продукт
    # ---------------------------------------------------------
    def report_movements_by_product(self, keyword):
        keyword = keyword.lower()
        movements = [
            m for m in self.movement_controller.get_all()
            if keyword in self.product_controller.get_by_id(m.product_id).name.lower()
        ]

        print(f"\n=== Движения за продукт: {keyword} ===")
        if not movements:
            print("Няма движения за този продукт.")
            return

        for m in movements:
            print(f"{m.date} | {m.movement_type.name} | Количество: {m.quantity} | Цена: {m.price}")

    # ---------------------------------------------------------
    # 4. Движения по тип (IN/OUT/MOVE)
    # ---------------------------------------------------------
    def report_movements_by_type(self, movement_type):
        movement_type = movement_type.upper()
        movements = [
            m for m in self.movement_controller.get_all()
            if m.movement_type.name == movement_type
        ]

        print(f"\n=== Движения от тип {movement_type} ===")
        if not movements:
            print("Няма такива движения.")
            return

        for m in movements:
            print(f"{m.date} | Продукт ID: {m.product_id} | Количество: {m.quantity}")

    # ---------------------------------------------------------
    # 5. Движения по дата
    # ---------------------------------------------------------
    def report_movements_by_date(self, date_str):
        movements = [
            m for m in self.movement_controller.get_all()
            if m.date.startswith(date_str)
        ]

        print(f"\n=== Движения за дата {date_str} ===")
        if not movements:
            print("Няма движения за тази дата.")
            return

        for m in movements:
            print(f"{m.date} | {m.movement_type.name} | Количество: {m.quantity}")

    # ---------------------------------------------------------
    # 6. Справка за продажби (всички фактури)
    # ---------------------------------------------------------
    def report_sales(self):
        invoices = self.invoice_controller.get_all()

        print("\n=== Справка за продажби ===")
        if not invoices:
            print("Няма продажби.")
            return

        total = 0
        for inv in invoices:
            print(f"{inv.date} | {inv.product} | {inv.quantity} бр. | {inv.total_price} лв. | Клиент: {inv.customer}")
            total += inv.total_price

        print(f"\nОбща стойност на продажбите: {total} лв.")

    # ---------------------------------------------------------
    # 7. Продажби по клиент
    # ---------------------------------------------------------
    def report_sales_by_customer(self, customer):
        invoices = self.invoice_controller.search_by_customer(customer)

        print(f"\n=== Продажби за клиент: {customer} ===")
        if not invoices:
            print("Няма продажби за този клиент.")
            return

        total = 0
        for inv in invoices:
            print(f"{inv.date} | {inv.product} | {inv.quantity} бр. | {inv.total_price} лв.")
            total += inv.total_price

        print(f"\nОбщо: {total} лв.")

    # ---------------------------------------------------------
    # 8. Продажби по продукт
    # ---------------------------------------------------------
    def report_sales_by_product(self, product):
        invoices = self.invoice_controller.search_by_product(product)

        print(f"\n=== Продажби за продукт: {product} ===")
        if not invoices:
            print("Няма продажби за този продукт.")
            return

        total = 0
        for inv in invoices:
            print(f"{inv.date} | {inv.customer} | {inv.quantity} бр. | {inv.total_price} лв.")
            total += inv.total_price

        print(f"\nОбщо: {total} лв.")

    # ---------------------------------------------------------
    # 9. Продажби по дата
    # ---------------------------------------------------------
    def report_sales_by_date(self, date_str):
        invoices = self.invoice_controller.search_by_date(date_str)

        print(f"\n=== Продажби за дата: {date_str} ===")
        if not invoices:
            print("Няма продажби за тази дата.")
            return

        total = 0
        for inv in invoices:
            print(f"{inv.product} | {inv.quantity} бр. | {inv.total_price} лв. | Клиент: {inv.customer}")
            total += inv.total_price

        print(f"\nОбщо: {total} лв.")
