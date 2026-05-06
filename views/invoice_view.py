from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table
from controllers.invoice_controller import InvoiceController
from models.user import User
from validators.invoice_validator import InvoiceValidator


class InvoiceView:
    def __init__(self, invoice_controller: InvoiceController, activity_log_controller=None):
        self.invoice_controller = invoice_controller
        self.activity_log = activity_log_controller


    def _input(self, prompt):
        value = input(prompt).strip()
        if value == "":
            return None
        return value


    def _show_invoices(self, invoices):
        if not invoices:
            print("\nНяма резултати.\n")
            return
        rows = []
        for inv in invoices:
            rows.append([inv.invoice_id[:8], inv.product, inv.customer, f"{inv.quantity} {inv.unit}",
                         f"{float(inv.total_price):.2f} лв.", inv.date[:16]])

        print("\n" + format_table(["ID", "Продукт", "Клиент", "Количество", "Общо", "Дата"], rows))

    def show_menu(self, user: User):
        while True:
            menu = self._build_menu()
            choice = menu.show()
            if menu.execute(choice, user) == "break":
                break

    def _build_menu(self):
        return Menu("Меню Фактури", [
            MenuItem("1", "Списък с всички фактури", self.show_all),
            MenuItem("2", "Преглед на фактура по ID", self.view_by_id),
            MenuItem("3", "Търсене по клиент", self.search_by_customer),
            MenuItem("4", "Търсене по продукт", self.search_by_product),
            MenuItem("5", "Търсене по дата", self.search_by_date),
            MenuItem("6", "Разширено търсене", self.advanced_search),
            MenuItem("7", "Търсене по сума", self.search_by_total),
            MenuItem("0", "Назад", lambda u: "break")])


    def show_all(self, user):
        self._show_invoices(self.invoice_controller.get_all())

    # Преглед по ID
    def view_by_id(self, user):
        print("\nПреглед на фактура по ID")

        while True:
            invoice_id = self._input("Въведете ID (UUID): ")
            if not invoice_id:
                print("Прекъснато.\n")
                return
            try:
                InvoiceValidator.validate_uuid(invoice_id, "Invoice ID")
            except ValueError as e:
                print(e)
                continue

            invoice = self.invoice_controller.get_by_id(invoice_id)
            if invoice:
                break

            print("Фактурата не е намерена.\n")

        columns = ["Поле", "Стойност"]
        rows = [["ID", invoice.invoice_id], ["Movement ID", invoice.movement_id],
                ["Продукт", invoice.product], ["Количество", f"{invoice.quantity} {invoice.unit}"],
                ["Единична цена", f"{invoice.unit_price} лв."],
                ["Общо", f"{invoice.total_price} лв."], ["Клиент", invoice.customer],
                ["Дата", invoice.date]]

        print("\n" + format_table(columns, rows))


    def search_by_customer(self, user):
        keyword = self._input("Клиент: ")
        if not keyword:
            print("Прекъснато.\n")
            return

        self._show_invoices(self.invoice_controller.search_by_customer(keyword))


    def search_by_product(self, user):
        keyword = self._input("Продукт: ")
        if not keyword:
            print("Прекъснато.\n")
            return

        self._show_invoices(self.invoice_controller.search_by_product(keyword))


    def search_by_date(self, user):
        while True:
            date_str = self._input("Дата (ГГГГ-ММ-ДД): ")
            if not date_str:
                print("Прекъснато.\n")
                return
            try:
                InvoiceValidator.validate_date(date_str)
                break
            except ValueError as e:
                print(e)

        self._show_invoices(self.invoice_controller.search_by_date(date_str))


    def advanced_search(self, user):
        print("\n   Разширено търсене   ")
        customer = self._input("Клиент: ")
        product = self._input("Продукт: ")
        start_date = self._input("Начална дата: ")
        end_date = self._input("Крайна дата: ")
        min_total = self._input("Минимална сума: ")
        max_total = self._input("Максимална сума: ")

        try:
            InvoiceValidator.validate_search_filters(start_date, end_date, min_total, max_total)
        except ValueError as e:
            print(e)
            return

        results = self.invoice_controller.advanced_search(customer=customer, product=product, start_date=start_date,
                                                          end_date=end_date, min_total=min_total, max_total=max_total)

        self._show_invoices(results)


    def search_by_total(self, user):
        print("\n   Търсене по сума   ")
        min_total = self._input("Минимална сума: ")
        max_total = self._input("Максимална сума: ")

        try:
            min_val = InvoiceValidator.parse_float(min_total, "Минимална сума") if min_total else None
            max_val = InvoiceValidator.parse_float(max_total, "Максимална сума") if max_total else None
        except ValueError as e:
            print(e)
            return
        self._show_invoices(self.invoice_controller.search_by_total(min_val, max_val))
