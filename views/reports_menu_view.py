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
        input("\nНатиснете Enter за връщане...")

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            menu_obj.execute(choice, user)

    def _search_flow(self, prompt, controller_fn, format_fn, title, headers):
        keyword = input(f"Въведете {prompt} (Enter за всички): ").strip()
        res = controller_fn(keyword) if keyword else controller_fn()
        self._display_report(title, headers, format_fn(res.data))

    def show_menu(self, user):
        menu = Menu("СПРАВКИ", [
            MenuItem("1", "Складови наличности", self.menu_inventory),
            MenuItem("2", "Логистика и движения", self.menu_logistics),
            MenuItem("3", "Продажби", self.menu_sales),
            MenuItem("4", "Анализ по FIFO", self.report_fifo_analysis),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    def menu_inventory(self, user):
        sub = Menu("НАЛИЧНОСТИ", [
            MenuItem("1", "Обобщена справка", self.summary_report),
            MenuItem("2", "Наличност по складове", self.inventory_by_warehouse),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(sub, user)

    def menu_logistics(self, user):
        sub = Menu("ЛОГИСТИКА", [
            MenuItem("1", "Хронологичен регистър", self.report_movements),
            MenuItem("2", "Търсене на доставки", self.search_delivery),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(sub, user)

    def menu_sales(self, user):
        sub = Menu("ПРОДАЖБИ", [
            MenuItem("1", "Всички продажби", self.report_sales),
            MenuItem("2", "Търсене по клиент", self.search_sales_by_customer),
            MenuItem("3", "Търсене по продукт", self.search_sales_by_product),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(sub, user)

    def _fmt_delivery(self, data):
        rows = []
        for i in data:
            rows.append([
                i["date"],
                i["movement_id"],
                i["product"],
                f"{i['quantity']} {i['unit']}",
                f"{float(i['price']):.2f}",
                i["supplier"]
            ])
        return rows

    def _fmt_sales(self, data):
        rows = []
        for i in data:
            rows.append([
                i["invoice_number"],
                i["date"],
                i["client"],
                i["product"],
                f"{float(i['total_price']):.2f}"
            ])
        return rows

    def summary_report(self, _):
        res = self.controller.report_inventory_summary()
        rows = []
        for i in res.data:
            rows.append([i["product"], i["available"], i["sold"], i["top_locations"]])
        self._display_report("Обобщена справка", ["Продукт", "Налично", "Продадено", "Локация"], rows)

    def inventory_by_warehouse(self, _):
        inv_data = self.controller.inventory_controller.data.get("products", {})
        loc_map = {loc.location_id: loc for loc in self.controller.location_controller.get_all()}
        rows = []

        for pid, pdata in inv_data.items():
            product = self.controller.product_controller.get_by_id(pid)
            p_name = product.name if product else f"Изтрит продукт ({pid[:8]})"
            p_unit = product.unit if product else "бр."

            for loc_id, qty in pdata.get("locations", {}).items():
                if float(qty) > 0:
                    loc_obj = loc_map.get(loc_id)
                    name = loc_obj.name if loc_obj else f"Склад {loc_id[:8]}"
                    rows.append([name, p_name, f"{float(qty):.2f} {p_unit}"])

        self._display_report("Наличност по складове", ["Склад", "Продукт", "Количество"], sorted(rows))

    def report_movements(self, _):
        res = self.controller.report_movements()
        rows = []
        for m in res.data:
            rows.append([
                m["date"],
                m["movement_id"],
                m["type"],
                m["product"],
                f"{m['quantity']} {m['unit']}",
                m["from"],
                m["to"]
            ])
        self._display_report("Хронология на движенията", ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"], rows)

    def search_delivery(self, _):
        headers = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"]
        self._search_flow("продукт или доставчик", self.controller.report_deliveries_all,
                          self._fmt_delivery, "Доставки", headers)

    def report_sales(self, _):
        res = self.controller.report_sales()
        self._display_report("Продажби", ["Фактура", "Дата", "Клиент", "Продукт", "Общо"], self._fmt_sales(res.data))

    def search_sales_by_customer(self, _):
        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Общо"]
        self._search_flow("име на клиент", self.controller.report_sales_by_customer,
                          self._fmt_sales, "Продажби", headers)

    def search_sales_by_product(self, _):
        headers = ["Фактура", "Дата", "Клиент", "Продукт", "Общо"]
        self._search_flow("име на продукт", self.controller.report_sales_by_product,
                          self._fmt_sales, "Продажби", headers)

    def report_fifo_analysis(self, _):
        while True:
            name = input("\nВъведете име или ID на продукт (или 'отказ' за изход): ").strip()
            if not name or name.lower() == 'отказ':
                break

            data = self.controller.product_lifecycle(name)
            if not data:
                print(f"Продукт '{name}' не е намерен.")
                continue

            print("\nАнализ по FIFO")
            print("------------------------------")
            print(f"Текуща наличност: {data['current_stock']} {data['unit']}")
            print(f"Общо движение: Вход: {data['total_in']} | Изход: {data['total_out']}")
            print("------------------------------")
            print(f"Приходи: {float(data['revenue']):.2f} лв.")
            print(f"Себестойност: {float(data['fifo_cost']):.2f} лв.")
            print(f"Печалба: {float(data['profit']):.2f} лв.")
            print("------------------------------")

            input("\nНатиснете Enter за връщане...")
            break
