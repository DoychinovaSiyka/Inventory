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
        lines.append("─" * 45)
        lines.append(f"ПРОДУКТ:          {item['product'].upper()}")
        lines.append(f"Общо количество:  {item['total']} {item['unit']}")
        lines.append("")
        lines.append("ПО СКЛАДОВЕ:")

        for wh, qty in item["warehouses"].items():
            lines.append(f"  • {wh}: {qty} {item['unit']}")

        lines.append("")
        lines.append(f"Доставено:        {item['delivered']}")
        lines.append(f"Продадено:        {item['sold']}")
        lines.append(f"Средна входна:    {item['avg_in_price']}")
        lines.append(f"Средна изходна:   {item['avg_out_price']}")
        lines.append(f"Последно:         {item['last_move']}")
        lines.append("─" * 45)
        return "\n".join(lines)

    def inventory_full_report(self, _):
        result = self.controller.report_inventory_full()
        print("\n ОБЕДИНЕН ОТЧЕТ ЗА НАЛИЧНОСТИТЕ ")
        for item in result.data:
            print(self.format_card(item))



    def report_movements(self, _):
        result = self.controller.report_movements()
        rows = []
        for m in result.data:
            quantity_text = f"{m['quantity']} {m['unit']}"
            rows.append([m["date"], m["movement_id"], m["type"], m["product"],
                         quantity_text, m["from"], m["to"]])

        headers = ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"]
        self._display_report("ХРОНОЛОГИЯ НА ДВИЖЕНИЯТА", headers, rows)



    def report_deliveries_all(self, _):
        result = self.controller.report_deliveries_all("")
        rows = []
        for item in result.data:
            rows.append([item["date"], item["movement_id"], item["product"],
                         f"{item['quantity']} {item['unit']}", item["price"], item["supplier"]])

        headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"]
        self._display_report("ВСИЧКИ ДОСТАВКИ (IN)", headers, rows)



    def report_sales_all(self, _):
        result = self.controller.report_sales()
        rows = []
        for item in result.data:
            rows.append([item["invoice_number"], item["date"], item["client"],
                         item["product"], item["total_price"], item.get("status", "АКТИВНА")])

        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Общо", "Статус"]
        self._display_report("ВСИЧКИ ПРОДАЖБИ", headers, rows)



    def report_fifo_analysis(self, _):
        while True:
            name = input("\nВъведете име или ID на продукт (или '0' за изход): ").strip()
            if not name or name == "0":
                break

            data = self.controller.fifo_analysis_for_product(name)
            if not data:
                print(f"Продукт '{name}' не е намерен.")
                continue

            print(f"\nАНАЛИЗ ПО FIFO ЗА: {data['product'].upper()}")
            print("─" * 40)
            print(f"Продадено количество: {data['total_out']} {data['unit']}")
            print(f"Приходи:              {data['revenue']:.2f} лв.")
            print(f"Себестойност (FIFO):  {data['fifo_cost']:.2f} лв.")
            print(f"Чиста печалба:        {data['profit']:.2f} лв.")
            print("─" * 40)
            break
