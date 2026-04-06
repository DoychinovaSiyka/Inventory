from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.invoice_controller import InvoiceController
from models.user import User


class InvoiceView:
    def __init__(self, invoice_controller: InvoiceController, activity_log_controller=None):
        self.invoice_controller = invoice_controller
        self.activity_log = activity_log_controller
        self.menu = self._build_menu()

    def show_menu(self, user: User):
        while True:
            choice = self.menu.show()
            result = self.menu.execute(choice, user)
            if result == "break":
                break

    def _build_menu(self):
        return Menu("Меню Фактури", [
            MenuItem("1", "Списък с всички фактури", self.show_all),
            MenuItem("2", "Преглед на фактура по ID", self.view_by_id),
            MenuItem("3", "Търсене по клиент", self.search_by_customer),
            MenuItem("4", "Търсене по продукт", self.search_by_product),
            MenuItem("5", "Търсене по дата (ГГГГ-ММ-ДД)", self.search_by_date),
            MenuItem("6", "Разширено търсене", self.advanced_search),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    #  Списък с всички фактури
    def show_all(self, user):
        invoices = self.invoice_controller.get_all()
        if not invoices:
            print("Няма налични фактури.")
            return

        if self.activity_log:
            self.activity_log.add_log(user.user_id, "VIEW_INVOICES", "Viewed all invoices")

        columns = ["ID", "Продукт", "Количество", "Ед. Цена", "Общо", "Клиент", "Дата"]
        rows = [[inv.invoice_id, inv.product, f"{inv.quantity} {inv.unit}", f"{inv.unit_price} лв.",
                 f"{inv.total_price} лв.", inv.customer, inv.date] for inv in invoices]
        print("\n" + format_table(columns, rows))

    #  Преглед по ID
    def view_by_id(self, user):
        invoice_id = input("Въведете ID на фактура (пълен UUID): ").strip()
        invoice = self.invoice_controller.get_by_id(invoice_id)

        if not invoice:
            print("Фактурата не е намерена.")
            return

        if self.activity_log:
            self.activity_log.add_log(user.user_id, "VIEW_INVOICE", f"Viewed invoice {invoice_id}")

        columns = ["Поле", "Стойност"]
        rows = [["ID", invoice.invoice_id], ["Movement ID", invoice.movement_id],
                ["Продукт", invoice.product], ["Количество", f"{invoice.quantity} {invoice.unit}"],
                ["Единична цена", f"{invoice.unit_price} лв."],
                ["Обща цена", f"{invoice.total_price} лв."], ["Клиент", invoice.customer],
                ["Дата", invoice.date]]

        print("\n" + format_table(columns, rows))

    #  Търсене по клиент
    def search_by_customer(self, user):
        keyword = input("Въведете име на клиент: ")
        results = self.invoice_controller.search_by_customer(keyword)
        if not results:
            print("Няма фактури за този клиент.")
            return

        if self.activity_log:
            self.activity_log.add_log(user.user_id, "SEARCH_INVOICE",
                                      f"Searched invoices by customer '{keyword}'")

        columns = ["ID", "Продукт", "Количество", "Общо", "Дата"]
        rows = [[inv.invoice_id, inv.product, f"{inv.quantity} {inv.unit}",
                 f"{inv.total_price} лв.", inv.date] for inv in results]

        print("\n" + format_table(columns, rows))

    #  Търсене по продукт
    def search_by_product(self, user):
        keyword = input("Въведете име на продукт: ")
        results = self.invoice_controller.search_by_product(keyword)
        if not results:
            print("Няма фактури за този продукт.")
            return

        if self.activity_log:
            self.activity_log.add_log(user.user_id, "SEARCH_INVOICE",
                                      f"Searched invoices by product '{keyword}'")

        columns = ["ID", "Клиент", "Количество", "Общо", "Дата"]
        rows = [[inv.invoice_id, inv.customer, f"{inv.quantity} {inv.unit}", f"{inv.total_price} лв.",
                 inv.date] for inv in results]

        print("\n" + format_table(columns, rows))

    #  Търсене по дата
    def search_by_date(self, user):
        date_str = input("Въведете дата (ГГГГ-ММ-ДД): ")
        results = self.invoice_controller.search_by_date(date_str)

        if not results:
            print("Няма фактури за тази дата.")
            return

        if self.activity_log:
            self.activity_log.add_log(user.user_id, "SEARCH_INVOICE",
                                      f"Searched invoices by date '{date_str}'")

        columns = ["ID", "Продукт", "Клиент", "Количество", "Общо"]
        rows = [[inv.invoice_id, inv.product, inv.customer, f"{inv.quantity} {inv.unit}",
             f"{inv.total_price} лв."] for inv in results]

        print("\n" + format_table(columns, rows))

    #  Разширено търсене
    def advanced_search(self, user):
        print("   Разширено търсене на фактури   ")
        customer = input("Клиент (или Enter за пропуск): ").strip() or None
        product = input("Продукт (или Enter за пропуск): ").strip() or None
        start_date = input("Начална дата (ГГГГ-ММ-ДД) или Enter: ").strip() or None
        end_date = input("Крайна дата (ГГГГ-ММ-ДД) или Enter: ").strip() or None

        # Ценови филтри — поправено преобразуване
        min_total_raw = input("Минимална обща стойност или Enter: ").strip()
        max_total_raw = input("Максимална обща стойност или Enter: ").strip()
        try:
            min_total = float(min_total_raw) if min_total_raw else None
            max_total = float(max_total_raw) if max_total_raw else None
        except ValueError:
            print("Невалидна стойност за цена.")
            return

        results = self.invoice_controller.advanced_search(customer=customer, product=product,
                                                          start_date=start_date, end_date=end_date,
                                                          min_total=min_total, max_total=max_total)

        if not results:
            print("\nНяма фактури, които отговарят на критериите.")
            return

        columns = ["ID", "Продукт", "Клиент", "Количество", "Общо", "Дата"]
        rows = [[inv.invoice_id, inv.product, inv.customer, f"{inv.quantity} {inv.unit}",
                 f"{inv.total_price} лв.", inv.date] for inv in results]

        print("\n" + format_table(columns, rows))

        if self.activity_log:
            self.activity_log.add_log(user.user_id, "ADVANCED_SEARCH_INVOICE",
                                      "Used advanced invoice search")
