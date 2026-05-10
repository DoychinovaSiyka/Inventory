from views.menu import Menu, MenuItem
from views.password_utils import format_table


class InvoiceView:
    def __init__(self, invoice_controller, activity_log_controller=None):
        self.invoice_controller = invoice_controller
        self.activity_log = activity_log_controller

    def _input(self, prompt):
        user_input = input(prompt).strip()
        if user_input == "":
            return None
        return user_input


    def _show_invoices(self, invoices):
        if not invoices:
            print("\nНяма намерени фактури.\n")
            return

        rows = []
        for inv in invoices:
            status_text = "V" if inv.is_active else "X (АНУЛИРАНА)"

            total = float(inv.total_price)
            total_display = f"{total:.2f} лв." if inv.is_active else f"[{total:.2f} лв.]"

            rows.append([inv.invoice_id[:8], inv.product[:15], inv.customer[:12],
                         f"{inv.quantity} {inv.unit}", total_display, status_text, inv.date[:16]])

        headers = ["ID (кратко)", "Продукт", "Клиент", "Количество", "Общо", "Статус", "Дата"]
        print("\n" + format_table(headers, rows))


    def show_menu(self, user):
        menu = Menu("Меню Фактури", [
            MenuItem("1", "Всички фактури (хронология)", self.show_all),
            MenuItem("2", "Само активни фактури", self.show_active_only),
            MenuItem("3", "Преглед по ID / Анулиране", self.view_by_id),
            MenuItem("4", "Търсене по клиент", self.search_by_customer),
            MenuItem("5", "Търсене по продукт", self.search_by_product),
            MenuItem("6", "Разширено търсене", self.advanced_search),
            MenuItem("0", "Назад", lambda u: "break")])

        while True:
            choice = menu.show()
            if choice in ("0", None):
                break
            if menu.execute(choice, user) == "break":
                break

    def show_all(self, _):
        """Показва всички записи, включително анулираните."""
        self._show_invoices(self.invoice_controller.get_all(include_cancelled=True))

    def show_active_only(self, _):
        self._show_invoices(self.invoice_controller.get_all(include_cancelled=False))

    def view_by_id(self, user):
        print("\nПРЕГЛЕД НА ФАКТУРА")
        invoice_id = self._input("Въведете ID (или част от него): ")
        if not invoice_id:
            return

        invoice = self.invoice_controller.get_by_id(invoice_id)
        if not invoice:
            print("Фактурата не е намерена.")
            return


        status_str = "АКТИВНА" if invoice.is_active else "АНУЛИРАНА"
        rows = [["Статус", status_str], ["Пълно ID", invoice.invoice_id],
                ["Продукт", invoice.product],
                ["Количество", f"{invoice.quantity} {invoice.unit}"],
                ["Ед. цена", f"{float(invoice.unit_price):.2f} лв."],
                ["ОБЩА СУМА", f"{float(invoice.total_price):.2f} лв."],
                ["Клиент", invoice.customer], ["Дата/Час", invoice.date]]

        print("\n" + format_table(["Детайл", "Стойност"], rows))


        if invoice.is_active:
            if self.invoice_controller.remove(invoice.invoice_id, user.user_id):
                print("\nФактурата беше успешно анулирана.")
            else:
                print("\nГрешка при анулиране.")
        else:
            print("\nТази фактура вече е анулирана.")


    def search_by_customer(self, _):
        keyword = self._input("\nИме на клиент: ")
        if keyword:
            results = self.invoice_controller.search_by_customer(keyword)
            self._show_invoices(results)

    def search_by_product(self, _):
        keyword = self._input("\nИме на продукт: ")
        if keyword:
            results = self.invoice_controller.search_by_product(keyword)
            self._show_invoices(results)

    def search_by_date(self, _):
        date_str = self._input("\nДата (ГГГГ-ММ-ДД): ")
        if date_str:
            try:
                results = self.invoice_controller.search_by_date(date_str)
                self._show_invoices(results)
            except Exception as e:
                print(f"Грешка: {e}")


    def advanced_search(self, _):
        customer = self._input("Клиент: ")
        product = self._input("Продукт: ")
        start_date = self._input("От дата (ГГГГ-ММ-ДД): ")
        end_date = self._input("До дата (ГГГГ-ММ-ДД): ")
        min_total = self._input("Минимална сума: ")
        max_total = self._input("Максимална сума: ")

        try:
            results = self.invoice_controller.advanced_search(customer=customer, product=product, start_date=start_date,
                                                              end_date=end_date, min_total=min_total, max_total=max_total)
            self._show_invoices(results)
        except Exception as e:
            print(f"\nГрешка при търсене: {e}")