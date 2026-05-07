from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table


class ReportsView:
    def __init__(self, controller):
        self.controller = controller

    def _display_report(self, title, headers, rows):
        if not rows:
            print("\nНяма налични данни за този отчет.\n")
            return
        print(f"\n--- {title} ---")
        print(format_table(headers, rows))
        input("\nНатиснете Enter за връщане...")

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None: break
            menu_obj.execute(choice, user)

    def _search_flow(self, prompt, controller_fn, format_fn, title, headers):
        keyword = input(f"Въведете {prompt}: ").strip()
        res = controller_fn(keyword) if keyword else controller_fn()
        self._display_report(title, headers, format_fn(res.data))

    def show_menu(self, user):
        menu = Menu("СПРАВКИ И СТРАТЕГИЧЕСКИ ОТЧЕТИ", [
            MenuItem("1", "Складови наличности", self.menu_inventory),
            MenuItem("2", "Логистика и Движения", self.menu_logistics),
            MenuItem("3", "Продажби и Търсене", self.menu_sales),
            MenuItem("4", "Финансов Анализ (FIFO)", self.report_fifo_analysis),
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
        # Тук използваме i["product"], което ReportController вече е взел от движението (историческо)
        return [[i["date"], i["movement_id"], i["product"],
                 f"{i['quantity']} {i['unit']}", f"{float(i['price']):.2f}", i["supplier"]] for i in data]

    def _fmt_sales(self, data):
        # Фактурите са snapshot, така че тук няма парадокс
        return [[i["invoice_number"], i["date"], i["client"],
                 i["product"], f"{float(i['total_price']):.2f}"] for i in data]

    def summary_report(self, _):
        res = self.controller.report_inventory_summary()
        rows = [[i["product"], i["available"], i["sold"], i["top_locations"]] for i in res.data]
        self._display_report("ОБОБЩЕНА СПРАВКА", ["Продукт", "Налично", "Продадено", "Локация"], rows)


    def inventory_by_warehouse(self, _):
        inv_data = self.controller.inventory_controller.data.get("products", {})
        loc_map = {loc.location_id: loc for loc in self.controller.location_controller.get_all()}
        rows = []

        # Вместо да въртим по продуктите в каталога, въртим по това, което РЕАЛНО има в склада
        for pid, pdata in inv_data.items():
            product = self.controller.product_controller.get_by_id(pid)
            # Ако продуктът е изтрит от каталога, показваме ID-то му или търсим последното му име
            p_name = product.name if product else f"Изтрит продукт ({pid[:8]})"
            p_unit = product.unit if product else "бр."

            for loc_id, qty in pdata.get("locations", {}).items():
                if float(qty) > 0:
                    name = loc_map[loc_id].name if loc_id in loc_map else f"Склад {loc_id[:8]}"
                    rows.append([name, p_name, f"{qty} {p_unit}"])

        self._display_report("ПО СКЛАДОВЕ", ["Склад", "Продукт", "Количество"], sorted(rows))

    def report_movements(self, _):
        res = self.controller.report_movements()
        # Използваме m["product"], който вече е историческото име от Movement
        rows = [[m["date"], m["movement_id"], m["type"], m["product"],
                 f"{m['quantity']} {m['unit']}", m["from"], m["to"]] for m in res.data]
        self._display_report("ХРОНОЛОГИЯ", ["Дата", "ID", "Тип", "Продукт", "Кол.", "От", "Към"], rows)

    def search_delivery(self, _):
        h = ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"]
        self._search_flow("продукт/доставчик", self.controller.report_deliveries_all,
                          self._fmt_delivery, "ДОСТАВКИ", h)

    def report_sales(self, _):
        res = self.controller.report_sales()
        self._display_report("ПРОДАЖБИ", ["Фактура", "Дата", "Клиент", "Продукт", "Общо"], self._fmt_sales(res.data))

    def search_sales_by_customer(self, _):
        h = ["Фактура", "Дата", "Клиент", "Продукт", "Общо"]
        self._search_flow("име на клиент", self.controller.report_sales_by_customer, self._fmt_sales, "ПРОДАЖБИ", h)

    def search_sales_by_product(self, _):
        h = ["Фактура", "Дата", "Клиент", "Продукт", "Общо"]
        self._search_flow("име на продукт", self.controller.report_sales_by_product, self._fmt_sales, "ПРОДАЖБИ", h)

    def report_fifo_analysis(self, _):
        name = input("Име на продукт за анализ: ").strip()
        if not name: return

        data = self.controller.product_lifecycle(name)
        if not data:
            print(f"\nПродукт '{name}' не е намерен.\n")
            return

        print("\n" + "═" * 50)
        print(f" СТРАТЕГИЧЕСКИ АНАЛИЗ: {data['product'].upper()}")
        print("═" * 50)
        print(f" Наличност: {data['current_stock']} {data['unit']}")
        print(f" Движение:  Вход: {data['total_in']} | Изход: {data['total_out']}")
        print("-" * 50)
        print(f" Приходи:   {float(data['revenue']):.2f} лв.")
        print(f" Разходи (FIFO): {float(data['fifo_cost']):.2f} лв.")
        print(f" Печалба:   {float(data['profit']):.2f} лв.")
        print("═" * 50)
        input("\nНатиснете Enter...")