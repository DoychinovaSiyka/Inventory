from datetime import datetime
from views.menu import Menu, MenuItem
from views.password_utils import format_table


class ReportsView:
    def __init__(self, controller):
        self.controller = controller


    def _check(self, data, msg="Няма данни."):
        if not data:
            print(f"\n{msg}\n")
            return False
        return True

    def _print_table(self, headers, rows):
        print(format_table(headers, rows))

    def _print_sales_table(self, data):
        if not self._check(data, "Няма продажби."):
            return
        rows = []
        for item in data:
            rows.append([item["invoice_number"], item["date"], item["client"], item["product"],
                         f"{item.get('unit_price', 0):.2f} лв.", f"{item['total_price']:.2f} лв."])
        self._print_table(["Фактура", "Дата", "Клиент", "Продукт", "Продажна цена", "Общо"], rows)

    def _print_delivery_table(self, data):
        if not self._check(data, "Няма доставки."):
            return
        rows = []
        for item in data:
            rows.append([item["date"], item["movement_id"], item["product"], f"{item['quantity']} {item['unit']}",
                         f"{item.get('price', 0):.2f} лв.", item["supplier"], item["location"]])
        self._print_table(["Дата", "ID", "Продукт", "Кол.", "Доставна цена", "Доставчик", "Склад"], rows)


    def _run_menu(self, menu_obj, user):
        while True:
            choice = menu_obj.show()
            if choice == "0" or choice is None:
                break
            menu_obj.execute(choice, user)


    def show_menu(self, user):
        menu = Menu("СПРАВКИ И ОТЧЕТИ", [
            MenuItem("1", "Наличности и складове", self.menu_inventory),
            MenuItem("2", "Движения (IN/OUT/MOVE)", self.menu_movements),
            MenuItem("3", "Продажби и фактури", self.menu_sales),
            MenuItem("4", "Доставки", self.menu_deliveries),
            MenuItem("5", "Финансови отчети", self.menu_finance),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(menu, user)


    def menu_inventory(self, user):
        submenu = Menu("НАЛИЧНОСТИ", [
            MenuItem("1", "Обобщена справка", self.summary_report),
            MenuItem("2", "Наличност по складове", self.inventory_by_warehouse),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)


    def menu_movements(self, user):
        submenu = Menu("ДВИЖЕНИЯ", [
            MenuItem("1", "Всички движения", self.report_movements),
            MenuItem("2", "Разширено филтриране", self.search_delivery),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)


    def menu_sales(self, user):
        submenu = Menu("ПРОДАЖБИ И ФАКТУРИ", [
            MenuItem("1", "Всички продажби", self.report_sales),
            MenuItem("2", "Търсене", self.search_sales),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)


    def menu_deliveries(self, user):
        submenu = Menu("ДОСТАВКИ", [
            MenuItem("1", "Всички доставки", self.report_all_deliveries),
            MenuItem("2", "Търсене", self.search_delivery),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)


    def menu_finance(self, user):
        submenu = Menu("ФИНАНСОВИ ОТЧЕТИ", [
            MenuItem("1", "Оборот по дни", self.report_turnover_by_day),
            MenuItem("2", "Най-продавани продукти", self.report_top_products),
            MenuItem("3", "Жизнен цикъл на продукт", self.report_lifecycle),
            MenuItem("0", "Назад", lambda u: "break")])
        self._run_menu(submenu, user)


    def summary_report(self, _):
        res = self.controller.report_inventory_summary()
        if not self._check(res.data):
            return
        rows = []
        for item in res.data:
            rows.append([item.get("product", "-"), item.get("available", "-"),
                         item.get("sold", "-"), item.get("top_locations", "-")])
        self._print_table(["Продукт", "Наличност", "Продадено", "Топ локации"], rows)

    def report_movements(self, _):
        res = self.controller.report_movements()
        if not self._check(res.data, "Няма движения."):
            return
        rows = []
        for m in res.data:
            rows.append([m.get("movement_id", "-"), m.get("date", "-"), m.get("type", "-"),
                         m.get("product", "-"), f"{m.get('quantity', 0)} {m.get('unit', '')}",
                         m.get("from", "-"), m.get("to", "-")])
        self._print_table(["ID", "Дата", "Тип", "Продукт", "Кол.", "От", "Към"], rows)

    def report_sales(self, _):
        res = self.controller.report_sales()
        self._print_sales_table(res.data)

    def report_all_deliveries(self, _):
        res = self.controller.report_deliveries_all()
        self._print_delivery_table(res.data)

    def search_delivery(self, _):
        key = input("Търсене: ").strip()
        if not key:
            print("Отказано.\n")
            return
        res = self.controller.report_deliveries_all(key)
        self._print_delivery_table(res.data)

    def search_sales(self, _):
        print("\nТърсене на продажба:")
        print("1. По клиент")
        print("2. По продукт")
        print("3. По дата")

        choice = input("Избор: ").strip()
        res = None
        if choice == "1":
            val = input("Клиент: ").strip()
            if val:
                res = self.controller.report_sales_by_customer(val)

        elif choice == "2":
            val = input("Продукт: ").strip()
            if val:
                res = self.controller.report_sales_by_product(val)

        elif choice == "3":
            val = input("Дата (ГГГГ-ММ-ДД): ").strip()
            try:
                d = datetime.strptime(val, "%Y-%m-%d")
                res = self.controller.report_sales_by_date(d)
            except:
                print("Невалидна дата.\n")
                return
        else:
            print("Невалиден избор.\n")
            return

        if res:
            self._print_sales_table(res.data)
        else:
            print("\nНяма данни или отказано.\n")

    def report_turnover_by_day(self, _):
        res = self.controller.report_turnover_by_day()
        if not self._check(res.data):
            return
        rows = []
        for item in res.data:
            rows.append([item["date"], item["count"], f"{item['total']:.2f} лв."])
        self._print_table(["Дата", "Брой", "Оборот"], rows)

    def report_top_products(self, _):
        res = self.controller.report_top_products()
        if not self._check(res.data, "Няма продажби."):
            return
        rows = []
        for item in res.data:
            rows.append([item["product"], f"{item['quantity']} {item['unit']}", f"{item['total']:.2f} лв."])
        self._print_table(["Продукт", "Количество", "Оборот"], rows)

    def inventory_by_warehouse(self, _):
        inventory_data = self.controller.inventory_controller.data.get("products", {})
        all_products = self.controller.product_controller.get_all()
        locations_map = {loc.location_id: loc for loc in self.controller.location_controller.get_all()}

        rows = []
        for product in all_products:
            pid = product.product_id
            p_inv = inventory_data.get(pid, {})
            locs = p_inv.get("locations", {})
            if not locs:
                total_stock = self.controller.inventory_controller.get_total_stock(pid)
                if total_stock > 0:
                    loc_obj = locations_map.get("W1")
                    loc_name = loc_obj.name if loc_obj else "W1"
                    rows.append([loc_name, product.name, f"{total_stock} {product.unit}"])
            else:
                for loc_id, qty in locs.items():
                    if float(qty) > 0:
                        loc = locations_map.get(loc_id)
                        loc_name = loc.name if loc else loc_id
                        rows.append([loc_name, product.name, f"{qty} {product.unit}"])

        if not rows:
            print("\nНяма налични продукти.\n")
            return

        rows.sort(key=lambda r: (r[0], r[1]))
        print("\n   Инвентар – наличност по складове\n")
        self._print_table(["Склад", "Продукт", "Наличност"], rows)

    # ЖИЗНЕН ЦИКЪЛ
    def report_lifecycle(self, _):
        name = input("Продукт: ").strip()
        if not name:
            return

        data = self.controller.product_lifecycle(name)
        if not data:
            print("\nПродуктът не е намерен.\n")
            return

        revenue = data.get("revenue", 0.0)
        cost_of_goods = data.get("fifo_cost", 0.0)
        profit = data.get("profit", 0.0)
        total_invested = data.get("expense", 0.0)
        total_in = data.get("total_in", 0.0)
        current_stock = data.get("current_stock", 0.0)

        if total_in > 0:
            avg_purchase_price = total_invested / total_in
        else:
            avg_purchase_price = 0.0

        in_stock_value = current_stock * avg_purchase_price

        print(f"   ФИНАНСОВ ОТЧЕТ: {data['product'].upper()}")
        print(f"  Наличност в склада: {current_stock} {data.get('unit', '')}")
        print(f"  Продадени бройки:   {data['total_out']} {data.get('unit', '')}")
        print("-" * 45)
        print(f"  ОБОРОТ (Продажби):        {revenue:>10.2f} лв.")
        print(f"  СЕБЕСТОЙНОСТ (Разход):    {cost_of_goods:>10.2f} лв.")
        print("-" * 45)
        print(f"  ЧИСТА ПЕЧАЛБА:            {profit:>10.2f} лв.")
        print(f"  * Стойност на стоката в склада: {in_stock_value:.2f} лв.")
        input("\nНатиснете Enter за продължение...")
