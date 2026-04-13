from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.report_controller import ReportController
from models.user import User


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
            MenuItem("0", "Назад", lambda u: "break")
        ])

    # Форматиране за визуализация (това е чиста View логика)
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

    # ПЕЧАТ НА ПРОДАЖБИ (View логика)
    def _print_sales(self, rows, has_id):
        columns = ["ID", "Продукт", "Количество", "Ед. Цена", "Общо", "Клиент", "Дата"]
        if not has_id:
            columns = columns[1:]
            rows = [row[1:] for row in rows]
        print(format_table(columns, rows))

    # СПРАВКИ – ПРОДАЖБИ
    def report_sales(self, _):
        result = self.controller.report_sales()
        if not result.data:
            print("\nНяма налични фактури или продажби.\n")
            return
        self._print_sales(result.rows, result.has_id)

    def report_sales_by_customer(self, _):
        customer = input("Клиент: ")
        result = self.controller.report_sales_by_customer(customer)
        if not result.data:
            print(f"\nНяма резултати за клиент: {customer}\n")
            return
        self._print_sales(result.rows, result.has_id)

    def report_sales_by_product(self, _):
        product = input("Продукт: ")
        result = self.controller.report_sales_by_product(product)
        if not result.data:
            print(f"\nНяма резултати за продукт: {product}\n")
            return
        self._print_sales(result.rows, result.has_id)

    def report_sales_by_date(self, _):
        date = input("Дата: ")
        result = self.controller.report_sales_by_date(date)
        if not result.data:
            print(f"\nНяма резултати за дата: {date}\n")
            return
        self._print_sales(result.rows, result.has_id)

    # СПРАВКА – НАЛИЧНОСТИ
    def report_stock(self, _):
        result = self.controller.report_stock()
        if not result.data:
            print("\nНяма налични продукти.\n")
            return

        rows = [
            [i['product'], self._format_qty(i['quantity'], i['product']), self._format_lv(i['price'])]
            for i in result.data
        ]
        print(format_table(["Продукт", "Количество", "Цена"], rows))

    # СПРАВКА – ДВИЖЕНИЯ
    def report_movements(self, _):
        result = self.controller.report_movements()
        if not result.data:
            print("\nНяма налични движения.\n")
            return

        print(format_table(
            ["Дата", "Тип", "ID", "Кол.", "Цена", "Склад"],
            result.rows
        ))
