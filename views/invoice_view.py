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

    # таблица с фиксирани ширини
    def _format_table_fixed(self, headers, rows, col_widths):
        line = "+" + "+".join("-" * w for w in col_widths) + "+"
        header_row = "|" + "|".join(f"{str(h):^{col_widths[i]}}" for i, h in enumerate(headers)) + "|"

        data_rows = []
        for r in rows:
            data_rows.append("|" + "|".join(f"{str(r[i]):^{col_widths[i]}}" for i in range(len(headers))) + "|")

        return "\n".join([line, header_row, line] + data_rows + [line])

    def show_menu(self, user: User):
        while True:
            menu = self._build_menu()
            choice = menu.show()
            result = menu.execute(choice, user)
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
            MenuItem("7", "Търсене по сума / диапазон", self.search_by_total),
            MenuItem("0", "Назад", lambda u: "break")
        ])


    def show_all(self, user):
        invoices = self.invoice_controller.get_all()
        if not invoices:
            print("Няма налични фактури.")
            return
        for inv in invoices:
            print("\n========== ФАКТУРА ==========")
            print(f"ID: {inv.invoice_id}")
            print(f"Movement ID: {inv.movement_id}")
            print(f"Продукт: {inv.product}")
            print(f"Количество: {inv.quantity} {inv.unit}")
            print(f"Единична цена: {inv.unit_price} лв.")
            print(f"Общо: {inv.total_price} лв.")
            print(f"Клиент: {inv.customer}")
            print(f"Дата: {inv.date}")
            print("==============================")

    # Преглед по ID
    def view_by_id(self, user):
        print("\nПреглед на фактура по ID")
        while True:
            invoice_id = input("Въведете ID на фактура (пълен UUID): ").strip()
            if not invoice_id:
                print("[!] Прекъснато – празен вход.\n")
                return
            try:
                InvoiceValidator.validate_uuid(invoice_id, "Invoice ID")
            except ValueError as e:
                print(f"[!] {e}")
                print("Моля, опитайте отново.\n")
                continue

            invoice = self.invoice_controller.get_by_id(invoice_id)
            if not invoice:
                print("Фактурата не е намерена.")
                print("Моля, опитайте отново.\n")
                continue

            break

        columns = ["Поле", "Стойност"]
        rows = [["ID", invoice.invoice_id], ["Movement ID", invoice.movement_id], ["Продукт", invoice.product],
                ["Количество", f"{invoice.quantity} {invoice.unit}"], ["Единична цена", f"{invoice.unit_price} лв."],
                ["Обща цена", f"{invoice.total_price} лв."], ["Клиент", invoice.customer], ["Дата", invoice.date]]

        print("\n" + format_table(columns, rows))

    # Търсене по клиент
    def search_by_customer(self, user):
        keyword = input("Въведете име на клиент: ").strip()
        if not keyword:
            print("[!] Прекъснато – празен вход.\n")
            return

        results = self.invoice_controller.search_by_customer(keyword)
        if results is None:
            print("[!] Невалиден клиент.")
            return
        if not results:
            print("[!] Няма такъв клиент.")
            return

        columns = ["ID", "Продукт", "Количество", "Общо", "Дата"]
        rows = [[inv.invoice_id, inv.product, f"{inv.quantity} {inv.unit}",
                 f"{inv.total_price} лв.", inv.date] for inv in results]

        print("\n" + self._format_table_fixed(columns, rows, [12, 40, 12, 12, 12]))

    # Търсене по продукт
    def search_by_product(self, user):
        keyword = input("Въведете име на продукт: ").strip()
        if not keyword:
            print("[!] Прекъснато – празен вход.\n")
            return

        results = self.invoice_controller.search_by_product(keyword)
        if results is None:
            print("[!] Невалиден продукт.")
            return
        if not results:
            print("[!] Няма такъв продукт.")
            return

        columns = ["ID", "Клиент", "Количество", "Общо", "Дата"]
        rows = [[inv.invoice_id, inv.customer, f"{inv.quantity} {inv.unit}",
                 f"{inv.total_price} лв.", inv.date] for inv in results]

        print("\n" + self._format_table_fixed(columns, rows, [12, 26, 12, 12, 12]))


    def search_by_date(self, user):
        while True:
            date_str = input("Въведете дата (ГГГГ-ММ-ДД): ").strip()
            if not date_str:
                print("[!] Прекъснато – празен вход.\n")
                return

            try:
                InvoiceValidator.validate_date(date_str)
                break
            except ValueError as e:
                print(f"[!] {e}")
                print("Моля, опитайте отново.\n")

        results = self.invoice_controller.search_by_date(date_str)
        if not results:
            print("[!] Няма фактури за тази дата.")
            return

        columns = ["ID", "Продукт", "Клиент", "Количество", "Общо"]
        rows = [[inv.invoice_id, inv.product, inv.customer, f"{inv.quantity} {inv.unit}",
                 f"{inv.total_price} лв."] for inv in results]

        print("\n" + self._format_table_fixed(columns, rows, [12, 40, 26, 12, 12]))


    def advanced_search(self, user):
        print("   Разширено търсене на фактури   ")
        customer = input("Клиент (или Enter): ").strip() or None
        product = input("Продукт (или Enter): ").strip() or None
        start_date = input("Начална дата (или Enter): ").strip() or None
        end_date = input("Крайна дата (или Enter): ").strip() or None
        min_total = input("Минимална стойност (или Enter): ").strip() or None
        max_total = input("Максимална стойност (или Enter): ").strip() or None

        try:
            InvoiceValidator.validate_search_filters(start_date, end_date, min_total, max_total)
        except ValueError as e:
            print(f"[!] {e}")
            return

        results = self.invoice_controller.advanced_search(customer=customer, product=product,
                                                          start_date=start_date, end_date=end_date,
                                                          min_total=min_total, max_total=max_total)
        if not results:
            print("\n[!] Няма фактури по тези критерии.")
            return

        columns = ["ID", "Продукт", "Клиент", "Количество", "Общо", "Дата"]
        rows = [[inv.invoice_id, inv.product, inv.customer, f"{inv.quantity} {inv.unit}",
                 f"{inv.total_price} лв.", inv.date] for inv in results]

        print("\n" + self._format_table_fixed(columns, rows, [12, 40, 26, 12, 12, 12]))

    # Търсене по сума / диапазон
    def search_by_total(self, user):
        print("   Търсене по сума / диапазон")
        min_total = input("Минимална сума (или Enter): ").strip()
        max_total = input("Максимална сума (или Enter): ").strip()
        try:
            min_val = InvoiceValidator.parse_float(min_total, "Минимална сума") if min_total else None
            max_val = InvoiceValidator.parse_float(max_total, "Максимална сума") if max_total else None
        except ValueError as e:
            print(f"[!] {e}")
            return

        results = self.invoice_controller.search_by_total(min_val, max_val)
        if not results:
            print("\nНяма фактури в този диапазон.\n")
            return

        columns = ["ID", "Продукт", "Клиент", "Количество", "Общо", "Дата"]
        rows = [[inv.invoice_id, inv.product, inv.customer,
                 f"{inv.quantity} {inv.unit}", f"{float(inv.total_price):.2f} лв.", inv.date] for inv in results]


        print(self._format_table_fixed(columns, rows, [12, 40, 26, 12, 12, 12]))
