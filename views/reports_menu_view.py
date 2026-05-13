from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table


class ReportsView:
    def __init__(self, controller):
        self.controller = controller


    def _display_report(self, title, headers, rows):
        if not rows:
            print("\nНяма данни за показване.\n")
            return
        print(f"\n{title}")
        print(format_table(headers, rows))


    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice in ("0", None):
                break
            if menu_obj.execute(choice, user) == "break":
                break

    def show_menu(self, user):
        menu = Menu("Отчети", [
            MenuItem("1", "Обединен отчет за наличностите", self.inventory_full_report),
            MenuItem("2", "Хронология на движенията", self.report_movements),
            MenuItem("3", "Всички доставки", self.report_deliveries_all),
            MenuItem("4", "Всички продажби", self.report_sales_all),
            MenuItem("5", "Анализ по FIFO", self.report_fifo_analysis),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    def format_card(self, item):
        lines = []
        lines.append("─" * 40)
        lines.append(f"Продукт:          {item['product']}")
        lines.append(f"Общо количество:  {item['total']}")
        lines.append("")
        lines.append("По складове:")


        for wh, qty in item["warehouses"].items():
            lines.append(f"  - {wh}: {qty}")

        lines.append("")
        lines.append(f"Доставено:        {item['delivered']}")
        lines.append(f"Продадено:        {item['sold']}")
        lines.append(f"Средна входна:    {item['avg_in_price']}")
        lines.append(f"Средна изходна:   {item['avg_out_price']}")
        lines.append(f"Последно движение:{item['last_move']}")
        lines.append("─" * 40)
        return "\n".join(lines)

    def inventory_full_report(self, _):
        result = self.controller.report_inventory_full()

        print("\nОБЕДИНЕН ОТЧЕТ – КАРТИ\n")

        for item in result.data:
            print(self.format_card(item))
            print()

    def report_movements(self, _):
        result = self.controller.report_movements()
        rows = []

        for m in result.data:
            quantity_text = f"{m['quantity']} {m['unit']}"
            rows.append([m["date"], m["movement_id"], m["type"], m["product"], quantity_text, m["from"], m["to"]])

        headers = ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"]
        self._display_report("Хронология на движенията", headers, rows)


    def report_deliveries_all(self, _):
        result = self.controller.report_deliveries_all("")
        rows = []

        for item in result.data:
            rows.append([item["date"], item["movement_id"], item["product"],
                         f"{item['quantity']} {item['unit']}", f"{float(item['price']):.2f} лв.", item["supplier"]])

        headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"]
        self._display_report("Всички доставки (IN)", headers, rows)


    def report_sales_all(self, _):
        result = self.controller.report_sales()
        rows = []

        for item in result.data:
            rows.append([item["invoice_number"], item["date"], item["client"],
                         item["product"], f"{float(item['total_price']):.2f} лв.", item.get("status", "АКТИВНА")])

        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Общо", "Статус"]
        self._display_report("Всички продажби", headers, rows)



    def report_fifo_analysis(self, _):
        while True:
            name = input("\nВъведете име или ID на продукт (или 'отказ'): ").strip()
            if not name or name.lower() == "отказ":
                break

            data = self.controller.product_lifecycle(name)
            if not data:
                print(f"Продукт '{name}' не е намерен.")
                continue

            print(f"\nАНАЛИЗ ПО FIFO ЗА: {data['product'].upper()}")
            print(f"Наличност: {data['current_stock']} {data['unit']}")
            print(f"История: Влезли: {data['total_in']} | Продадени: {data['total_out']}")
            print(f"Приходи: {data['revenue']:.2f} лв.")
            print(f"Себестойност: {data['fifo_cost']:.2f} лв.")
            print(f"Печалба: {data['profit']:.2f} лв.")
            break
