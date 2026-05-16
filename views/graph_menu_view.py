from views.menu import Menu, MenuItem
from graph.warehouse import Warehouse
from graph.warehouse_graph import WarehouseGraph
from models.user import User


class GraphView:
    def __init__(self, inventory_controller, location_controller, product_controller):
        self.inventory_controller = inventory_controller
        self.location_controller = location_controller
        self.product_controller = product_controller
        self.graph = WarehouseGraph()
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
        product = None
        for p in self.product_controller.get_all():
            if p.name.lower() == product_name.lower():
                product = p
                break

        if not product:
            return []


        product_id = str(product.product_id)

        for loc in self.location_controller.get_all():

            warehouse_code = loc.code
            warehouse_uuid = str(loc.location_id)

            if not warehouse_code:
                continue

            qty = self.inventory_controller.get_stock(product_id, warehouse_uuid)
            if qty > 0:
                result.append((warehouse_code, qty))

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
        product_name = input("\nИме на стока (Enter = отказ): ").strip()
        if not product_name:
            print("Операцията е отказана.")
            return

        my_location = input("Вашето ID (напр. W1, Enter = отказ): ").strip().upper()
        if not my_location:
            print("Операцията е отказана.")
            return
        if my_location not in self.graph.nodes:
            print(f"Локация '{my_location}' не съществува.")
            print(f"Достъпни: {', '.join(self.graph.nodes.keys())}")
            return

        # Взимаме складовете с наличност
        sources = self._get_warehouses_with_product(product_name)

        if not sources:
            print(f"'{product_name}' не е наличен в нито един склад.")
            return

        all_sources = [wid.upper() for wid, qty in sources]
        other_sources = [s for s in all_sources if s != my_location]
        if not other_sources:
            print(f"'{product_name}' се среща само в {my_location}.")
            return

        distances, predecessors = self.graph.dijkstra(my_location)

        reachable = [s for s in other_sources if distances.get(s, float('inf')) < float('inf')]

        if not reachable:
            print(f"\nИма складове с наличност ({', '.join(other_sources)}), но няма път до тях.")
            return

        best_source = min(reachable, key=lambda s: distances[s])
        shortest_distance = distances[best_source]

        path = []
        step = best_source
        while step is not None:
            path.append(step)
            if step == my_location:
                break
            step = predecessors.get(step)
        path.reverse()

        source_name = self.graph.nodes[best_source].name

        print("\n         ЛОГИСТИЧЕН АНАЛИЗ (Dijkstra)")
        print(f"  Продукт:    {product_name}")
        print(f"  Източник:   {source_name} ({best_source})")
        print(f"  Разстояние: {shortest_distance} км")
        print(f"  Маршрут:    {' -> '.join(path)}")
