from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.report_controller import ReportController
from models.user import User
from datetime import datetime


class ReportsView:
    def __init__(self, controller: ReportController):
        self.controller = controller
        self.location_controller = controller.location_controller
        self.menu = self._build_menu()

    def show_menu(self, user: User):
        while True:
            choice = self.menu.show()
            if self.menu.execute(choice, user) == "break":
                break

    def _build_menu(self):
        return Menu("Справки и Отчети", [
            MenuItem("1", "Справка за наличности", self.report_stock),
            MenuItem("2", "Справка за движения", self.report_movements),
            MenuItem("3", "Всички фактури/продажби", self.report_sales),
            MenuItem("4", "Търсене по клиент", self.report_sales_by_customer),
            MenuItem("5", "Търсене по продукт", self.report_sales_by_product),
            MenuItem("6", "Търсене по дата", self.report_sales_by_date),
            MenuItem("7", "Справка за всички доставки", self.report_all_deliveries),
            MenuItem("8", "Търсене на доставка", self.search_delivery),
            MenuItem("9", "Оборот по дни", self.report_turnover_by_day),
            MenuItem("10", "Най-продавани продукти", self.report_top_products),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    # Форматиране за визуализация
    @staticmethod
    def _clean_none(value, replacement="—"):
        return replacement if value is None else str(value)

    @staticmethod
    def _format_lv(value):
        try:
            val = round(float(value), 2)
            return f"{val:.2f} лв."
        except:
            return "0.00 лв."

    @staticmethod
    def _format_qty(value, product_name=""):
        try:
            if value is None:
                return "0 бр."
            val = float(value)
            display_val = int(val) if val.is_integer() else round(val, 2)
            name = str(product_name).lower()
            unit = "кг" if any(x in name for x in ["брашно", "захар", "домати", "кг"]) else "бр."
            return f"{display_val} {unit}"
        except:
            return str(value)

    # СПРАВКИ – ПРОДАЖБИ
    def report_sales(self, _):
        result = self.controller.report_sales()
        if not result.data:
            print("\nНяма налични фактури или продажби.\n")
            return

        rows = [[item.get("invoice_number"), item.get("date"), item.get("client"), item.get("product"),
                 self._format_lv(item.get("total_amount"))] for item in result.data]

        print(format_table(["№ Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))

    def report_sales_by_customer(self, _):
        customer = input("Клиент: ")
        result = self.controller.report_sales_by_customer(customer)
        if not result.data:
            print(f"\nНяма резултати за клиент: {customer}\n")
            return

        rows = [[item.get("invoice_number"), item.get("date"), item.get("client"), item.get("product"),
                 self._format_lv(item.get("total_amount"))] for item in result.data]

        print(format_table(["№ Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))

    def report_sales_by_product(self, _):
        product = input("Продукт: ")
        result = self.controller.report_sales_by_product(product)
        if not result.data:
            print(f"\nНяма резултати за продукт: {product}\n")
            return

        rows = [[item.get("invoice_number"), item.get("date"), item.get("client"), item.get("product"),
                 self._format_lv(item.get("total_amount"))] for item in result.data]

        print(format_table(["№ Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))

    # СПРАВКА – ТЪРСЕНЕ ПО ДАТА
    def report_sales_by_date(self, _):
        date_str = input("Дата (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("\nНевалиден формат на дата! Използвайте YYYY-MM-DD.\n")
            return

        result = self.controller.report_sales_by_date(date_str)
        if not result.data:
            print(f"\nНяма резултати за дата: {date_str}\n")
            return

        rows = [[item.get("invoice_number"), item.get("date"),
                 item.get("client"), item.get("product"), self._format_lv(item.get("total_amount"))]
                for item in result.data]

        print(format_table(["№ Фактура", "Дата", "Клиент", "Продукт", "Общо"], rows))

    # СПРАВКА – НАЛИЧНОСТИ
    def report_stock(self, _):
        result = self.controller.report_stock()
        if not result.data:
            print("\nНяма налични продукти.\n")
            return
        rows = [[i['product'], self._format_qty(i['quantity'], i['product']),
                 self._format_lv(i['price'])] for i in result.data]
        print(format_table(["Продукт", "Количество", "Цена"], rows))

    # СПРАВКА – ДВИЖЕНИЯ
    def report_movements(self, _):
        result = self.controller.report_movements()
        if not result.data:
            print("\nНяма налични движения.\n")
            return
        rows = [[item.get("date"), item.get("type"), item.get("movement_id"), item.get("quantity"), item.get("price"),
                 item.get("location_name")] for item in result.data]

        print(format_table(["Дата", "Тип", "ID", "Кол.", "Цена", "Склад"], rows))

    # СПРАВКА – ВСИЧКИ ДОСТАВКИ
    def report_all_deliveries(self, _):
        result = self.controller.report_deliveries_all()  # ← КОРЕКЦИЯ
        if not result.data:
            print("\nНяма доставки.\n")
            return

        rows = [[item.get("date"), item.get("movement_id"), item.get("product"), item.get("quantity"),
                 item.get("supplier"), item.get("location_name")] for item in result.data]
        print(format_table(["Дата", "ID", "Продукт", "Количество", "Доставчик", "Склад"], rows))

    # ТЪРСЕНЕ НА ДОСТАВКА
    def search_delivery(self, _):
        keyword = input("Търсене (ID, продукт, доставчик, дата): ").strip()
        result = self.controller.report_deliveries_search(keyword)  # ← КОРЕКЦИЯ

        if not result.data:
            print("\nНяма намерени доставки.\n")
            return

        rows = [[item.get("date"), item.get("movement_id"), item.get("product"), item.get("quantity"),
                 item.get("supplier"), item.get("location_name")] for item in result.data]
        print(format_table(["Дата", "ID", "Продукт", "Количество", "Доставчик", "Склад"], rows))

    # Оборот по дни
    def report_turnover_by_day(self, _):
        result = self.controller.report_turnover_by_day()
        if not result.data:
            print("\nНяма продажби за показване.\n")
            return

        rows = [[item["date"], item["count"], f"{item['total']:.2f} лв."] for item in result.data]
        print(format_table(["Дата", "Брой продажби", "Оборот"], rows))

    # Топ продукти
    def report_top_products(self, _):
        result = self.controller.report_top_products()
        if not result.data:
            print("\nНяма продажби.\n")
            return
        rows = [[item["product"], item["quantity"], f"{item['total']:.2f} лв."] for item in result.data]
        print(format_table(["Продукт", "Продадено количество", "Оборот"], rows))
