

from menus.menu import Menu, MenuItem
from storage.password_utils import format_table
from controllers.invoice_controller import InvoiceController
from models.user import User


class InvoiceView:
    def __init__(self, invoice_controller: InvoiceController):
        self.invoice_controller = invoice_controller

    def show_menu(self, user: User):
        menu = Menu("Меню Фактури", [
            MenuItem("1", "Списък с всички фактури", self.show_all),
            MenuItem("2", "Преглед на фактура по ID", self.view_by_id),
            MenuItem("3", "Търсене по клиент", self.search_by_customer),
            MenuItem("4", "Търсене по продукт", self.search_by_product),
            MenuItem("5", "Търсене по дата (ГГГГ-ММ-ДД)", self.search_by_date),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, user)
            if result == "break":
                break

    # 1. Списък с всички фактури
    def show_all(self, user: User):
        invoices = self.invoice_controller.get_all()

        if not invoices:
            print("Няма налични фактури.")
            return

        columns = ["ID", "Продукт", "Количество", "Ед. Цена", "Общо", "Клиент", "Дата"]
        rows = [
            [
                inv.invoice_id,
                inv.product,
                f"{inv.quantity} {inv.unit}",
                inv.unit_price,
                inv.total_price,
                inv.customer,
                inv.date
            ]
            for inv in invoices
        ]

        print("\n" + format_table(columns, rows))

    # 2. Преглед по ID
    def view_by_id(self, user: User):
        invoice_id = input("Въведете ID на фактура: ")
        invoice = self.invoice_controller.get_by_id(invoice_id)

        if not invoice:
            print("Фактурата не е намерена.")
            return

        columns = ["Поле", "Стойност"]
        rows = [
            ["ID", invoice.invoice_id],
            ["Movement ID", invoice.movement_id],
            ["Продукт", invoice.product],
            ["Количество", f"{invoice.quantity} {invoice.unit}"],
            ["Единична цена", invoice.unit_price],
            ["Обща цена", invoice.total_price],
            ["Клиент", invoice.customer],
            ["Дата", invoice.date]
        ]

        print("\n" + format_table(columns, rows))

    # 3. Търсене по клиент
    def search_by_customer(self, user: User):
        keyword = input("Въведете име на клиент: ")
        results = self.invoice_controller.search_by_customer(keyword)

        if not results:
            print("Няма фактури за този клиент.")
            return

        columns = ["ID", "Продукт", "Количество", "Общо", "Дата"]
        rows = [
            [
                inv.invoice_id,
                inv.product,
                f"{inv.quantity} {inv.unit}",     # ← НОВО
                inv.total_price,
                inv.date
            ]
            for inv in results
        ]

        print("\n" + format_table(columns, rows))

    # 4. Търсене по продукт
    def search_by_product(self, user: User):
        keyword = input("Въведете име на продукт: ")
        results = self.invoice_controller.search_by_product(keyword)

        if not results:
            print("Няма фактури за този продукт.")
            return

        columns = ["ID", "Клиент", "Количество", "Общо", "Дата"]
        rows = [
            [
                inv.invoice_id,
                inv.customer,
                f"{inv.quantity} {inv.unit}",
                inv.total_price,
                inv.date
            ]
            for inv in results
        ]

        print("\n" + format_table(columns, rows))

    # 5. Търсене по дата
    def search_by_date(self, user: User):
        date_str = input("Въведете дата (ГГГГ-ММ-ДД): ")
        results = self.invoice_controller.search_by_date(date_str)

        if not results:
            print("Няма фактури за тази дата.")
            return

        columns = ["ID", "Продукт", "Клиент", "Количество", "Общо"]
        rows = [
            [
                inv.invoice_id,
                inv.product,
                inv.customer,
                f"{inv.quantity} {inv.unit}",
                inv.total_price
            ]
            for inv in results
        ]

        print("\n" + format_table(columns, rows))
