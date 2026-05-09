from views.menu import Menu, MenuItem
from views.password_utils import format_table


class InvoiceView:
    def __init__(self, invoice_controller, activity_log_controller=None):
        self.invoice_controller = invoice_controller
        self.activity_log = activity_log_controller

    def _input(self, prompt):
        value = input(prompt).strip()
        return value if value != "" else None

    def _show_invoices(self, invoices):
        """показване на фактури в таблица."""
        if not invoices:
            print("\nНяма намерени фактури.\n")
            return

        rows = []
        for inv in invoices:
            total = float(inv.total_price)
            rows.append([inv.invoice_id[:8], inv.product, inv.customer,
                         f"{inv.quantity} {inv.unit}", f"{total:.2f} лв.", inv.date[:16]])

        print("\n" + format_table(
            ["ID (кратко)", "Продукт", "Клиент", "Количество", "Общо", "Дата"], rows))

    def show_menu(self, user):
        menu = Menu("Меню Фактури", [
            MenuItem("1", "Списък с всички", self.show_all),
            MenuItem("2", "Преглед по ID", self.view_by_id),
            MenuItem("3", "Търсене по клиент", self.search_by_customer),
            MenuItem("4", "Търсене по продукт", self.search_by_product),
            MenuItem("5", "Търсене по дата", self.search_by_date),
            MenuItem("6", "Разширено търсене", self.advanced_search),
            MenuItem("0", "Назад", lambda u: "break")])

        while True:
            choice = menu.show()
            if choice == "0" or choice is None: break
            menu.execute(choice, user)

    def show_all(self, _):
        self._show_invoices(self.invoice_controller.get_all())

    def view_by_id(self, _):
        print("\nПРЕГЛЕД НА ФАКТУРА")
        invoice_id = self._input("Въведете ID (или част от него): ")
        if not invoice_id: return

        invoice = self.invoice_controller.get_by_id(invoice_id)
        if not invoice:
            print("Фактурата не е намерена.")
            return


        rows = [["Пълно ID", invoice.invoice_id], ["Продукт", invoice.product],
                ["Количество", f"{invoice.quantity} {invoice.unit}"],
                ["Ед. цена", f"{float(invoice.unit_price):.2f} лв."],
                ["ОБЩА СУМА", f"{float(invoice.total_price):.2f} лв."],
                ["Клиент", invoice.customer], ["Дата/Час", invoice.date]]
        print("\n" + format_table(["Детайл", "Стойност"], rows))
        input("\nНатиснете Enter за продължение...")

    def search_by_customer(self, _):
        keyword = self._input("\nИме на клиент: ")
        if keyword:
            self._show_invoices(self.invoice_controller.search_by_customer(keyword))

    def search_by_product(self, _):
        keyword = self._input("\nИме на продукт: ")
        if keyword:
            self._show_invoices(self.invoice_controller.search_by_product(keyword))

    def search_by_date(self, _):
        date_str = self._input("\nДата (ГГГГ-ММ-ДД): ")
        if date_str:
            try:
                self._show_invoices(self.invoice_controller.search_by_date(date_str))
            except Exception as e:
                print(f"Грешка: {e}")


    def advanced_search(self, _):
        print("\nРАЗШИРЕНО ТЪРСЕНЕ (Enter за пропускане)")
        customer = self._input("Клиент: ")
        product = self._input("Продукт: ")
        start_date = self._input("От дата (ГГГГ-ММ-ДД): ")
        end_date = self._input("До дата (ГГГГ-ММ-ДД): ")
        min_total = self._input("Минимална сума: ")
        max_total = self._input("Максимална сума: ")

        try:
            results = self.invoice_controller.advanced_search(customer=customer, product=product,
                                                              start_date=start_date,
                                                              end_date=end_date, min_total=min_total,
                                                              max_total=max_total)
            self._show_invoices(results)
        except Exception as e:
            print(f"\nГрешка при търсене: {e}")