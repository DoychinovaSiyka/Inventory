# views/reports_view.py

from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.report_controller import ReportController
from models.user import User


class ReportsView:
    def __init__(self, controller: ReportController):
        self.controller = controller

    def show_menu(self, user: User):
        menu = Menu("Справки", [
            MenuItem("1", "Справка за наличности", self.report_stock),
            MenuItem("2", "Справка за движения", self.report_movements),
            MenuItem("3", "Справка за продажби", self.report_sales),
            MenuItem("4", "Справка за продажби по клиент", self.report_sales_by_customer),
            MenuItem("5", "Справка за продажби по продукт", self.report_sales_by_product),
            MenuItem("6", "Справка за продажби по дата", self.report_sales_by_date),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # 1. Наличности
    def report_stock(self, _):
        report = self.controller.report_stock()
        rows = [
            [item["product"], item["quantity"], item["price"], item["location"]]
            for item in report.data
        ]
        print(format_table(["Продукт", "Количество", "Цена", "Локация"], rows))

    # 2. Движения
    def report_movements(self, _):
        print("\n1. Всички движения")
        print("2. По продукт")
        print("3. По тип движение (IN/OUT/MOVE)")
        print("4. По дата (ГГГГ-ММ-ДД)")

        sub = input("Избор: ")

        # 2.1 Всички движения
        if sub == "1":
            report = self.controller.report_movements()
            rows = [
                [item["date"], item["type"], item["product_id"], item["quantity"], item["price"], item["location"]]
                for item in report.data
            ]
            print(format_table(["Дата", "Тип", "Продукт ID", "Количество", "Цена", "Локация"], rows))

        # 2.2 По продукт
        elif sub == "2":
            keyword = input("Име на продукт: ")
            report = self.controller.report_movements_by_product(keyword)
            rows = [
                [item["date"], item["type"], item["quantity"], item["price"]]
                for item in report.data
            ]
            print(format_table(["Дата", "Тип", "Количество", "Цена"], rows))

        # 2.3 По тип движение
        elif sub == "3":
            mtype = input("Тип движение (IN/OUT/MOVE): ").upper()
            report = self.controller.report_movements_by_type(mtype)
            rows = [
                [item["date"], item["product_id"], item["quantity"]]
                for item in report.data
            ]
            print(format_table(["Дата", "Продукт ID", "Количество"], rows))

        # 2.4 По дата
        elif sub == "4":
            date_str = input("Дата (ГГГГ-ММ-ДД): ")
            report = self.controller.report_movements_by_date(date_str)
            rows = [
                [item["date"], item["type"], item["quantity"]]
                for item in report.data
            ]
            print(format_table(["Дата", "Тип", "Количество"], rows))

        else:
            print("Невалиден избор.")

    # 3. Продажби (общо)
    def report_sales(self, _):
        report = self.controller.report_sales()
        rows = [
            [item["date"], item["product"], item["quantity"], item["total_price"], item["customer"]]
            for item in report.data
        ]
        print(format_table(["Дата", "Продукт", "Количество", "Общо", "Клиент"], rows))

    # 4. Продажби по клиент
    def report_sales_by_customer(self, _):
        customer = input("Име на клиент: ")
        report = self.controller.report_sales_by_customer(customer)
        rows = [
            [item["date"], item["product"], item["quantity"], item["total_price"]]
            for item in report.data
        ]
        print(format_table(["Дата", "Продукт", "Количество", "Общо"], rows))

    # 5. Продажби по продукт
    def report_sales_by_product(self, _):
        product = input("Име на продукт: ")
        report = self.controller.report_sales_by_product(product)
        rows = [
            [item["date"], item["customer"], item["quantity"], item["total_price"]]
            for item in report.data
        ]
        print(format_table(["Дата", "Клиент", "Количество", "Общо"], rows))

    # 6. Продажби по дата
    def report_sales_by_date(self, _):
        date_str = input("Дата (ГГГГ-ММ-ДД): ")
        report = self.controller.report_sales_by_date(date_str)
        rows = [
            [item["product"], item["customer"], item["quantity"], item["total_price"]]
            for item in report.data
        ]
        print(format_table(["Продукт", "Клиент", "Количество", "Общо"], rows))
