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
            print("\n--- Няма намерени фактури ---\n")
            return
        rows = []
        for inv in invoices:
            try:
                total = float(inv.total_price)
            except (ValueError, TypeError):
                total = 0.0

            rows.append([inv.invoice_id[:8], inv.product, inv.customer,
                         f"{inv.quantity} {inv.unit}", f"{total:.2f} лв.", inv.date[:16]])

        print("\n" + format_table(["ID (кратко)", "Продукт", "Клиент", "Количество", "Общо", "Дата"], rows))

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

    def view_by_id(self, user):
        print("\n=== Преглед на фактура по ID ===")
        while True:
            invoice_id = self._input("Въведете ID: ")
            if not invoice_id:
                print("Прекъснато.\n")
                return

            invoice = self.invoice_controller.get_by_id(invoice_id)
            if invoice:
                break
            print("Фактура с такова ID не е намерена. Опитайте отново.\n")


        try:
            u_price = float(invoice.unit_price)
            t_price = float(invoice.total_price)
        except (ValueError, TypeError):
            u_price = 0.0
            t_price = 0.0


        m_id = invoice.movement_id[:8] if (hasattr(invoice, 'movement_id') and invoice.movement_id) else "-"

        columns = ["Поле", "Стойност"]
        rows = [["Пълно ID", invoice.invoice_id], ["Движение ID", invoice.movement_id[:8]],
                ["Продукт", invoice.product], ["Количество", f"{invoice.quantity} {invoice.unit}"],
                ["Единична цена", f"{invoice.unit_price:.2f} лв."], ["Общо", f"{invoice.total_price:.2f} лв."],
                ["Клиент", invoice.customer], ["Дата", invoice.date]]

        print("\n" + format_table(columns, rows))

    def search_by_customer(self, user):
        keyword = self._input("Въведете име на клиент: ")
        if not keyword: return
        self._show_invoices(self.invoice_controller.search_by_customer(keyword))

    def search_by_product(self, user):
        keyword = self._input("Въведете име на продукт: ")
        if not keyword: return
        self._show_invoices(self.invoice_controller.search_by_product(keyword))

    def search_by_date(self, user):
        while True:
            date_str = self._input("Дата (ГГГГ-ММ-ДД): ")
            if not date_str: return
            try:
                InvoiceValidator.validate_date(date_str)
                break
            except ValueError as e:
                print(f"{e}")
        self._show_invoices(self.invoice_controller.search_by_date(date_str))

    def advanced_search(self, user):
        print("\n--- Разширено търсене ---")
        customer = self._input("Клиент: ")
        product = self._input("Продукт: ")
        start_date = self._input("Начална дата (ГГГГ-ММ-ДД): ")
        end_date = self._input("Крайна дата (ГГГГ-ММ-ДД): ")
        min_total = self._input("Минимална сума: ")
        max_total = self._input("Максимална сума: ")

        try:
            InvoiceValidator.validate_search_filters(start_date, end_date, min_total, max_total)
            results = self.invoice_controller.advanced_search(customer=customer, product=product,
                                                               start_date=start_date, end_date=end_date,
                                                               min_total=min_total, max_total=max_total)
            self._show_invoices(results)
        except ValueError as e:
            print(f"{e}")

    def search_by_total(self, user):
        print("\n--- Търсене по сума ---")
        min_total = self._input("Минимална сума: ")
        max_total = self._input("Максимална сума: ")

        try:
            min_val = InvoiceValidator.parse_float(min_total, "Минимална сума") if min_total else None
            max_val = InvoiceValidator.parse_float(max_total, "Максимална сума") if max_total else None
            results = self.invoice_controller.advanced_search(min_total=min_val, max_total=max_val)
            self._show_invoices(results)
        except ValueError as e:
            print(f"{e}")