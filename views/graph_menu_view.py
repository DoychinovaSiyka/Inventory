from views.menu import Menu, MenuItem
from graph.warehouse import Warehouse
from graph.warehouse_graph import WarehouseGraph
from models.user import User

from controllers.inventory_controller import InventoryController
from controllers.location_controller import LocationController
from controllers.product_controller import ProductController






class GraphView:
    def __init__(self, inventory_controller: InventoryController, location_controller: LocationController,
                 product_controller: ProductController):
        self.inventory_controller = inventory_controller
        self.location_controller = location_controller
        self.product_controller = product_controller

        self.graph: WarehouseGraph = WarehouseGraph()

        self._setup_network()


    def _setup_network(self):
        warehouses = [Warehouse("W1", "София"), Warehouse("W2", "Пловдив"),
                      Warehouse("W3", "Варна"), Warehouse("W4", "Бургас"),
                      Warehouse("W5", "Магазин Смолян")]

        for w in warehouses:
            self.graph.add_warehouse(w)

        edges = [("W1", "W2", 150), ("W2", "W4", 250), ("W4", "W3", 130), ("W1", "W5", 250), ("W5", "W3", 350)]
        for start, end, dist in edges:
            self.graph.add_edge(start, end, dist)
            self.graph.add_edge(end, start, dist)




    def _get_warehouses_with_product(self, product_name):
        result = []
        has_any = False

        # За всеки склад проверяваме количеството от инвентара
        for loc in self.location_controller.get_all():
            warehouse_code = loc.code
            warehouse_uuid = str(loc.location_id)

            qty = self.inventory_controller.get_stock_by_name(product_name, warehouse_uuid)

            if qty > 0:
                has_any = True
                result.append((warehouse_code, qty))

        if not has_any:
            return []

        return result







    def _build_menu(self):
        return Menu("Логистичен Модул (Dijkstra)",
            [MenuItem("1", "Намери най-близка наличност", self.calculate_best_delivery),
             MenuItem("0", "Назад", lambda u: "break")])





    def show_menu(self, user: User):
        while True:
            menu = self._build_menu()
            choice = menu.show()
            if menu.execute(choice, user) == "break":
                break





    def calculate_best_delivery(self, user: User):
        product_name = input("\nИме на стока: ").strip()
        if not product_name:
            return

        while True:
            min_raw = input("Минимално количество: ").strip()
            max_raw = input("Максимално количество: ").strip()

            try:
                min_threshold = float(min_raw) if min_raw else 0.0
                max_threshold = float(max_raw) if max_raw else float('inf')
            except ValueError:
                print("Грешка: въведете валидни числа.")
                continue

            if min_threshold < 0:
                print("Минималното количество не може да е отрицателно.")
                continue

            if max_threshold < min_threshold:
                print("Максимумът трябва да е >= минимумът.")
                continue

            break

        my_location = input("Вашето ID (напр. W1): ").strip().upper()
        if not my_location or my_location not in self.graph.nodes:
            print(f"Грешка: Локация '{my_location}' не съществува.")
            return

        sources = self._get_warehouses_with_product(product_name)
        if not sources:
            print(f"'{product_name}' не е наличен никъде.")
            return

        other_sources = [(wid.upper(), qty) for wid, qty in sources if wid.upper() != my_location]
        if not other_sources:
            print(f"'{product_name}' е наличен само при Вас ({my_location}).")
            return


        filtered = []
        for wid, qty in other_sources:
            if min_threshold <= qty <= max_threshold:
                filtered.append(wid)

        if not filtered:
            print("Няма складове, които отговарят на количествените условия.")
            return

        distances, predecessors = self.graph.dijkstra(my_location)

        reachable = [s for s in filtered if distances.get(s, float('inf')) < float('inf')]
        if not reachable:
            print("\nИма складове с наличност, но няма маршрут до тях.")
            return

        best_source = min(reachable, key=lambda s: distances[s])
        path = self.graph.reconstruct_path(my_location, best_source, predecessors)
        path_with_names = [f"{self.graph.nodes[node].name} ({node})" for node in path]

        print("\n" + "=" * 40)
        print("         ЛОГИСТИЧЕН АНАЛИЗ")
        print("=" * 40)
        print(f"  Продукт:    {product_name}")
        print(f"  Източник:   {self.graph.nodes[best_source].name} ({best_source})")
        print(f"  Разстояние: {distances[best_source]} км")
        print(f"  Маршрут:    {' -> '.join(path_with_names)}")
        print("=" * 40)
