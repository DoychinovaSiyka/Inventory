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
            if choice == "0" or choice is None:
                break
            if menu_obj.execute(choice, user) == "break":
                break

    def _search_flow(self, prompt, controller_fn, format_fn, title, headers):
        keyword = input(f"Въведете {prompt} (Enter за всички): ").strip()
        result = controller_fn(keyword)
        formatted_data = format_fn(result.data)
        full_title = title

        try:
            total = result.summary["total_revenue"]
            full_title = f"{title} (Общ оборот: {total:.2f} лв.)"
        except:
            pass

        self._display_report(full_title, headers, formatted_data)





    def show_menu(self, user):
        menu = Menu("Отчети", [
            MenuItem("1", "Обединен отчет за наличностите", self.inventory_full_report),
            MenuItem("2", "Хронология на движенията", self.report_movements),
            MenuItem("3", "Доставки", self.search_delivery),
            MenuItem("4", "Продажби", self.report_sales_combined),
            MenuItem("5", "Анализ по FIFO", self.report_fifo_analysis),
            MenuItem("0", "Назад", lambda u: "break")
        ])
        self._run_menu(menu, user)





    # ОБЕДИНЕН ОТЧЕТ ЗА НАЛИЧНОСТИТЕ
    def inventory_full_report(self, _):
        result = self.controller.report_inventory_full()

        rows = []
        for item in result.data:
            rows.append([
                item["product"],
                item["total"],
                item["warehouses"],
                item["delivered"],
                item["sold"],
                item["avg_in_price"],
                item["avg_out_price"],
                item["last_move"]
            ])

        headers = [
            "Продукт",
            "Общо",
            "По складове",
            "Доставено",
            "Продадено",
            "Средна входна",
            "Средна изходна",
            "Последно движение"
        ]

        self._display_report("Обединен отчет за наличностите", headers, rows)




    def report_movements(self, _):
        result = self.controller.report_movements()
        rows = []
        for m in result.data:
            quantity_text = f"{m['quantity']} {m['unit']}"
            rows.append([m["date"], m["movement_id"], m["type"], m["product"], quantity_text, m["from"], m["to"]])

        self._display_report("Хронология на движенията",
                             ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"], rows)

    def _fmt_delivery(self, data):
        rows = []
        for item in data:
            price_value = float(item["price"])
            quantity_text = f"{item['quantity']} {item['unit']}"
            rows.append([item["date"], item["movement_id"], item["product"],
                         quantity_text, f"{price_value:.2f} лв.", item["supplier"]])
        return rows

    def search_delivery(self, _):
        headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"]
        self._search_flow("продукт или доставчик",
                          self.controller.report_deliveries_all,
                          self._fmt_delivery,
                          "Доставки (IN)",
                          headers)

    def _fmt_sales(self, data):
        rows = []
        for item in data:
            total_value = float(item.get("total_price", 0))
            status = item.get("status", "АКТИВНА")
            rows.append([item["invoice_number"], item["date"], item["client"],
                         item["product"], f"{total_value:.2f} лв.", status])
        return rows

    def report_sales_combined(self, _):
        keyword = input("\nВъведете клиент или продукт (Enter за всички): ").strip()
        if not keyword:
            result = self.controller.report_sales()
            sales = result.data
        else:
            sales_by_customer = self.controller.report_sales_by_customer(keyword).data
            sales_by_product = self.controller.report_sales_by_product(keyword).data
            sales = sales_by_customer[:]
            for item in sales_by_product:
                if item not in sales:
                    sales.append(item)

        formatted = self._fmt_sales(sales)
        title = f"Продажби ({len(sales)} резултата)"
        self._display_report(title,
                             ["Фактура", "Дата", "Клиент", "Продукт", "Общо", "Статус"],
                             formatted)

    def report_fifo_analysis(self, _):
        while True:
            name = input("\nВъведете име или ID на продукт (или 'отказ' за изход): ").strip()
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

