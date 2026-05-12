from views.menu import Menu, MenuItem
from views.password_utils import format_table


class InvoiceView:
    def __init__(self, invoice_controller):
        self.invoice_controller = invoice_controller

    def _input(self, prompt):
        value = input(prompt).strip()
        if value == "":
            return None
        return value

    def _show_invoices(self, invoices):
        """Показва фактури в таблица."""
        if not invoices:
            print("\nНяма намерени фактури.\n")
            return

        rows = []
        for inv in invoices:
            status_text = "V" if inv.is_active else "X (АНУЛИРАНА)"
            total = float(inv.total_price)
            total_display = f"{total:.2f} лв." if inv.is_active else f"[{total:.2f} лв.]"

            rows.append([inv.invoice_id[:8], inv.product, inv.customer, f"{inv.quantity} {inv.unit}",
                         total_display, status_text, inv.date])

        headers = ["ID", "Продукт", "Клиент", "Количество", "Общо", "Статус", "Дата"]
        print("\n" + format_table(headers, rows))

    def show_menu(self, user):
        menu = Menu("Меню Фактури", [
            MenuItem("1", "Активни фактури", self.show_all),
            MenuItem("2", "Анулиране по ID", self.view_by_id),
            MenuItem("0", "Назад", lambda u: "break")])

        while True:
            choice = menu.show()
            if choice in ("0", None):
                break
            if menu.execute(choice, user) == "break":
                break

    def show_all(self, _):
        """Показва само активните фактури."""
        invoices = self.invoice_controller.get_all(include_cancelled=False)
        self._show_invoices(invoices)

    def view_by_id(self, user):
        invoice_id = self._input("\nВъведете ID (8 символа): ")
        if not invoice_id:
            return

        invoice = self.invoice_controller.get_by_id(invoice_id)
        if not invoice:
            print("Фактурата не е намерена.")
            return

        status_str = "АКТИВНА" if invoice.is_active else "АНУЛИРАНА"

        rows = [ ["Статус", status_str], ["Пълно ID", invoice.invoice_id], ["Продукт", invoice.product],
                 ["Количество", f"{invoice.quantity} {invoice.unit}"],
                 ["Ед. цена", f"{float(invoice.unit_price):.2f} лв."], ["ОБЩА СУМА", f"{float(invoice.total_price):.2f} лв."],
                 ["Клиент", invoice.customer], ["Дата/Час", str(invoice.date)]]

        print("\n" + format_table(["Детайл", "Стойност"], rows))

        short_id = invoice.invoice_id[:8]

        if invoice.is_active:
            if self.invoice_controller.remove(short_id, user.user_id):
                print("\nФактурата беше успешно анулирана.")
            else:
                print("\nГрешка при анулиране.")
        else:
            print("\nТази фактура вече е анулирана.")
