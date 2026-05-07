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
        print(f"\n=== {title} ===")
        print(format_table(headers, rows))
        input("\nНатиснете Enter за връщане към менюто...")

    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            menu_obj.execute(choice, user)

    def show_menu(self, user):
        menu = Menu("СПРАВКИ И СТРАТЕГИЧЕСКИ ОТЧЕТИ", [
            MenuItem("1", "Складов Капитал (Наличности)", self.menu_inventory),
            MenuItem("2", "Логистичен Одит (Движения)", self.menu_logistics),
            MenuItem("3", "Продажби и Фактуриране", self.menu_sales),
            MenuItem("4", "Бизнес Анализи (Финанси)", self.menu_finance),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)

    def menu_inventory(self, user):
        submenu = Menu("СКЛАДОВИ НАЛИЧНОСТИ", [
            MenuItem("1", "Обобщена справка (Всичко)", self.summary_report),
            MenuItem("2", "Наличност по конкретни складове", self.inventory_by_warehouse),
            MenuItem("3", "Обща стойност на склада (FIFO)", self.total_value_report),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def menu_logistics(self, user):
        submenu = Menu("ЛОГИСТИКА И ДВИЖЕНИЯ", [
            MenuItem("1", "Пълен хронологичен регистър", self.report_movements),
            MenuItem("2", "Справка Доставки (IN)", self.report_all_deliveries),
            MenuItem("3", "Търсене на конкретна доставка", self.search_delivery),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def menu_sales(self, user):
        submenu = Menu("ПРОДАЖБИ И ФАКТУРИ", [
            MenuItem("1", "Всички продажби", self.report_sales),
            MenuItem("2", "Търсене по филтри", self.menu_search_sales),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def menu_search_sales(self, user):
        submenu = Menu("ТЪРСЕНЕ НА ПРОДАЖБИ", [
            MenuItem("1", "По клиент", self.search_sales_by_customer),
            MenuItem("2", "По продукт", self.search_sales_by_product),
            MenuItem("3", "По дата (ГГГГ-ММ-ДД)", self.search_sales_by_date),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def menu_finance(self, user):
        submenu = Menu("ФИНАНСОВИ АНАЛИЗИ", [
            MenuItem("1", "Тренд: Оборот по дни", self.report_turnover_by_day),
            MenuItem("2", "Най-продавани продукти (ТОП 10)", self.report_top_products),
            MenuItem("3", "Жизнен цикъл и рентабилност", self.report_lifecycle),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    def summary_report(self, _):
        res = self.controller.report_inventory_summary()
        rows = [[i.get("product", "-"), i.get("available", "-"), i.get("sold", "-"), i.get("top_locations", "-")] for i
                in res.data]
        self._display_report("ОБОБЩЕНА СКЛАДОВА СПРАВКА", ["Продукт", "Налично", "Продадено", "Топ локации"], rows)

    def inventory_by_warehouse(self, _):
        # Тук използваме логиката, която вече имаш
        inventory_data = self.controller.inventory_controller.data.get("products", {})
        all_products = self.controller.product_controller.get_all()
        locations_map = {loc.location_id: loc for loc in self.controller.location_controller.get_all()}

        rows = []
        for product in all_products:
            p_inv = inventory_data.get(product.product_id, {})
            for loc_id, qty in p_inv.get("locations", {}).items():
                if float(qty) > 0:
                    loc = locations_map.get(loc_id)
                    loc_display = f"{loc.name} ({loc_id[:8]})" if loc else loc_id[:8]
                    rows.append([loc_display, product.name, f"{qty} {product.unit}"])

        rows.sort(key=lambda r: (r[0], r[1]))
        self._display_report("НАЛИЧНОСТ ПО СКЛАДОВЕ", ["Склад (ID)", "Продукт", "Количество"], rows)

    def total_value_report(self, _):
        total = self.controller.inventory_controller.get_total_inventory_value_fifo(self.controller.movement_controller)
        print("\n" + "=" * 55)
        print(f" ОБЩА ФИНАНСОВА СТОЙНОСТ НА СКЛАДА (FIFO): {total:>10.2f} лв.")
        print("=" * 55)
        input("\nНатиснете Enter...")

    def report_movements(self, _):
        res = self.controller.report_movements()
        rows = [[str(m.get("movement_id", ""))[:8], str(m.get("date", ""))[5:16], m.get("type", "-"),
                 m.get("product", "-"), f"{m.get('quantity', 0)} {m.get('unit', '')}",
                 m.get("from", "-"), m.get("to", "-")] for m in res.data]
        self._display_report("ХРОНОЛОГИЯ НА ВСИЧКИ ДВИЖЕНИЯ", ["ID", "Дата/Час", "Тип", "Продукт", "Кол.", "От", "Към"],
                             rows)

    def report_all_deliveries(self, _):
        res = self.controller.report_deliveries_all()
        self._print_deliveries(res.data)

    def search_delivery(self, _):
        key = input("Въведете продукт или доставчик за търсене: ").strip()
        if key:
            res = self.controller.report_deliveries_all(key)
            self._print_deliveries(res.data)

    def _print_deliveries(self, data):
        rows = [[i["date"][5:16], i["movement_id"][:8], i["product"], f"{i['quantity']} {i['unit']}",
                 f"{i.get('price', 0):.2f} лв.", i["supplier"]] for i in data]
        self._display_report("СПРАВКА ДОСТАВКИ (IN)", ["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"], rows)

    def report_sales(self, _):
        res = self.controller.report_sales()
        self._print_sales(res.data)

    def _print_sales(self, data):
        rows = [[i["invoice_number"][:8], i["date"][5:16], i["client"], i["product"],
                 f"{i.get('unit_price', 0):.2f}", f"{i['total_price']:.2f}"] for i in data]
        self._display_report("РЕГИСТЪР НА ПРОДАЖБИТЕ", ["Фактура", "Дата", "Клиент", "Продукт", "Цена", "Общо лв."],
                             rows)

    def search_sales_by_customer(self, _):
        val = input("Име на клиент: ").strip()
        if val: self._print_sales(self.controller.report_sales_by_customer(val).data)

    def search_sales_by_product(self, _):
        val = input("Име на продукт: ").strip()
        if val: self._print_sales(self.controller.report_sales_by_product(val).data)

    def search_sales_by_date(self, _):
        val = input("Дата (ГГГГ-ММ-ДД): ").strip()
        try:
            datetime.strptime(val, "%Y-%m-%d")
            self._print_sales(self.controller.report_sales_by_date(val).data)
        except ValueError:
            print("Невалиден формат.")

    def report_turnover_by_day(self, _):
        res = self.controller.report_turnover_by_day()
        rows = [[i["date"], i["count"], f"{i['total']:.2f} лв."] for i in res.data]
        self._display_report("ТРЕНД: ДНЕВЕН ОБОРОТ", ["Дата", "Брой продажби", "Оборот"], rows)

    def report_top_products(self, _):
        res = self.controller.report_top_selling_products(limit=10)
        rows = [[f"{idx}.", i["name"], i["total_qty"], f"{i['total_revenue']:.2f} лв."] for idx, i in
                enumerate(res.data, 1)]
        self._display_report("ТОП 10 НАЙ-ПРОДАВАНИ ПРОДУКТИ", ["№", "Продукт", "Количество", "Общ приход"], rows)

    def report_lifecycle(self, _):
        name = input("Въведете име на продукт за анализ: ").strip()
        if not name: return
        data = self.controller.product_lifecycle(name)
        if not data:
            print("\nПродуктът не е намерен.\n")
            return

        rev, cost, profit = data.get("revenue", 0.0), data.get("fifo_cost", 0.0), data.get("profit", 0.0)
        margin = (profit / rev * 100) if rev > 0 else 0.0
        status = "ПЕЧЕЛИВШ" if margin > 15 else ("ЗАГУБА!" if profit < 0 else "НИСЪК МАРЖ")

        print("\n" + "═" * 50 + f"\n  ФИНАНСОВ АНАЛИЗ: {data['product'].upper()}\n  Статус: {status}\n" + "═" * 50)
        print(f"  Текуща наличност: {data.get('current_stock', 0)} {data.get('unit', '')}")
        print(f"  Общо продадени:   {data.get('total_out', 0)} {data.get('unit', '')}\n" + "-" * 50)
        print(
            f"  ПРИХОДИ:         {rev:>12.2f} лв.\n  РАЗХОДИ (FIFO):  {cost:>12.2f} лв.\n  ЧИСТА ПЕЧАЛБА:   {profit:>12.2f} лв.\n  МАРЖ:            {margin:>12.2f} %\n" + "═" * 50)
        input("\nНатиснете Enter...")