from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table


class ReportsView:
    def __init__(self, controller):
        self.controller = controller

    def _check(self, data, msg="Няма налични данни за този отчет."):
        if not data:
            print(f"\n[!] {msg}\n")
            return False
        return True

    def _print_table(self, headers, rows):
        print(format_table(headers, rows))

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
            MenuItem("4", "БИЗНЕС АНАЛИЗИ (Финанси)", self.menu_finance),
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
            MenuItem("3", "ЖИЗНЕН ЦИКЪЛ И РЕНТАБИЛНОСТ", self.report_lifecycle),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)

    # --- КОНКРЕТНИ ОТЧЕТИ (ИНВЕНТАР) ---
    def summary_report(self, _):
        res = self.controller.report_inventory_summary()
        if not self._check(res.data): return
        rows = []
        for item in res.data:
            rows.append([item.get("product", "-"), item.get("available", "-"),
                         item.get("sold", "-"), item.get("top_locations", "-")])
        self._print_table(["Продукт", "Налично", "Продадено", "Топ локации"], rows)
        input("\nНатиснете Enter...")

    def inventory_by_warehouse(self, _):
        inventory_data = self.controller.inventory_controller.data.get("products", {})
        all_products = self.controller.product_controller.get_all()
        locations_map = {loc.location_id: loc for loc in self.controller.location_controller.get_all()}

        rows = []
        for product in all_products:
            pid = product.product_id
            p_inv = inventory_data.get(pid, {})
            locs = p_inv.get("locations", {})
            for loc_id, qty in locs.items():
                if float(qty) > 0:
                    loc = locations_map.get(loc_id)
                    loc_name = loc.name if loc else loc_id
                    rows.append([loc_name, product.name, f"{qty} {product.unit}"])

        if not self._check(rows, "Складовете са празни."): return
        rows.sort(key=lambda r: (r[0], r[1]))
        print("\n--- НАЛИЧНОСТ ПО СКЛАДОВЕ ---")
        self._print_table(["Склад", "Продукт", "Количество"], rows)
        input("\nНатиснете Enter...")

    def total_value_report(self, _):
        total = self.controller.inventory_controller.get_total_inventory_value_fifo(self.controller.movement_controller)
        print("\n" + "=" * 50)
        print(f" ОБЩА ФИНАНСОВА СТОЙНОСТ НА СКЛАДА (FIFO): {total:>10.2f} лв.")
        print("=" * 50)
        input("\nНатиснете Enter...")

    # --- КОНКРЕТНИ ОТЧЕТИ (ЛОГИСТИКА) ---
    def report_movements(self, _):
        res = self.controller.report_movements()
        if not self._check(res.data, "Няма регистрирани движения."): return
        rows = []
        for m in res.data:
            # СИНХРОН: Кратко ID (8) и съкратена дата
            rows.append([str(m.get("movement_id", ""))[:8], str(m.get("date", ""))[5:16],
                         m.get("type", "-"), m.get("product", "-"),
                         f"{m.get('quantity', 0)} {m.get('unit', '')}",
                         m.get("from", "-"), m.get("to", "-")])
        print("\n--- ХРОНОЛОГИЯ НА ВСИЧКИ ДВИЖЕНИЯ ---")
        self._print_table(["ID", "Дата/Час", "Тип", "Продукт", "Кол.", "От", "Към"], rows)
        input("\nНатиснете Enter...")

    # --- КОНКРЕТНИ ОТЧЕТИ (ПРОДАЖБИ) ---
    def _print_sales_table(self, data):
        if not self._check(data, "Няма намерени продажби."): return
        rows = []
        for item in data:
            rows.append([item["invoice_number"][:8], item["date"][5:16], item["client"],
                         item["product"], f"{item.get('unit_price', 0):.2f}", f"{item['total_price']:.2f}"])
        self._print_table(["Фактура", "Дата", "Клиент", "Продукт", "Цена", "Общо лв."], rows)
        input("\nНатиснете Enter...")

    def report_sales(self, _):
        res = self.controller.report_sales()
        self._print_sales_table(res.data)

    # --- КОНКРЕТНИ ОТЧЕТИ (АНАЛИЗИ) ---
    def report_turnover_by_day(self, _):
        res = self.controller.report_turnover_by_day()
        if not self._check(res.data): return
        rows = []
        for item in res.data:
            rows.append([item["date"], item["count"], f"{item['total']:.2f} лв."])
        print("\n--- ДНЕВЕН ОБОРОТ ---")
        self._print_table(["Дата", "Брой продажби", "Оборот"], rows)
        input("\nНатиснете Enter...")

    def report_lifecycle(self, _):
        """АВТОМАТИЗИРАН БИЗНЕС АНАЛИЗ"""
        name = input("Продукт за анализ (Име): ").strip()
        if not name: return
        data = self.controller.product_lifecycle(name)
        if not data:
            print("\n[!] Продуктът не е намерен.\n")
            return

        rev = data.get("revenue", 0.0)
        cost = data.get("fifo_cost", 0.0)
        profit = data.get("profit", 0.0)
        margin = (profit / cost * 100) if cost > 0 else 0.0

        status = "ПЕЧЕЛИВШ" if margin > 15 else "НИСЪК МАРЖ"
        if profit < 0: status = "ЗАГУБА!"

        print(f"\n>>> ФИНАНСОВ АНАЛИЗ: {data['product'].upper()} <<<")
        print(f"Статус на рентабилност: {status}")
        print("-" * 50)
        print(f" Наличност:       {data.get('current_stock', 0)} {data.get('unit', '')}")
        print(f" Продадени:       {data.get('total_out', 0)} {data.get('unit', '')}")
        print("-" * 50)
        print(f" ПРИХОДИ:         {rev:>10.2f} лв.")
        print(f" РАЗХОДИ (FIFO):  {cost:>10.2f} лв.")
        print(f" ЧИСТА ПЕЧАЛБА:   {profit:>10.2f} лв.")
        print(f" МАРЖ:            {margin:>10.2f} %")
        print("-" * 50)
        input("\nНатиснете Enter...")

    # Помощни търсачки (СИНХРОНИЗИРАНИ)
    def search_sales_by_customer(self, _):
        val = input("Име на клиент: ").strip()
        if val: self._print_sales_table(self.controller.report_sales_by_customer(val).data)

    def search_sales_by_product(self, _):
        val = input("Име на продукт: ").strip()
        if val: self._print_sales_table(self.controller.report_sales_by_product(val).data)

    def search_sales_by_date(self, _):
        val = input("Дата (ГГГГ-ММ-ДД): ").strip()
        try:
            d = datetime.strptime(val, "%Y-%m-%d")
            self._print_sales_table(self.controller.report_sales_by_date(d).data)
        except:
            print("[!] Невалиден формат.")

    def report_all_deliveries(self, _):
        res = self.controller.report_deliveries_all()
        if not self._check(res.data, "Няма заприходени доставки."): return
        rows = []
        for i in res.data:
            rows.append([i["date"][5:16], i["movement_id"][:8], i["product"],
                         f"{i['quantity']} {i['unit']}", f"{i.get('price', 0):.2f}", i["supplier"]])
        self._print_table(["Дата", "ID", "Продукт", "Кол.", "Цена", "Доставчик"], rows)
        input("\nНатиснете Enter...")

    def search_delivery(self, _):
        key = input("Ключова дума за търсене: ").strip()
        if not key: return
        res = self.controller.report_deliveries_all(key)
        self.report_all_deliveries(res)