from views.menu import Menu, MenuItem
from graph.warehouse import Warehouse
from graph.warehouse_graph import WarehouseGraph
from models.user import User


class GraphView:
    def __init__(self, inventory_controller, location_controller=None):
        self.inventory_controller = inventory_controller
        self.location_controller = location_controller
        self.graph = WarehouseGraph()
        # Подготвяме мрежата от складове и разстоянията между тях
        self._setup_network()

    def _setup_network(self):
        warehouses = [Warehouse("W1", "София"), Warehouse("W2", "Пловдив"),
                      Warehouse("W3", "Варна"), Warehouse("W4", "Бургас"),
                      Warehouse("W5", "Магазин Смолян")]

        for w in warehouses:
            self.graph.add_warehouse(w)

        # ПРАВИМ ПЪТИЩАТА ДВУПОСОЧНИ
        edges = [("W1", "W2", 150), ("W2", "W4", 250), ("W4", "W3", 130), ("W1", "W5", 250), ("W5", "W3", 350)]

        for start, end, dist in edges:
            self.graph.add_edge(start, end, dist)
            self.graph.add_edge(end, start, dist)

    def _build_menu(self):
        # Менюто съдържа основната функция – търсене на най-близък склад
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
        """Намира най-близкия склад, в който се среща продуктът. Разглежда всички случаи:
        наличен / неналичен / един склад / много складове / няма път."""

        product_name = input("\nИме на стока (Enter = отказ): ").strip()
        if not product_name:
            print("Операцията е отказана.")
            return

        my_location = input("Вашето ID (напр. W1, Enter = отказ): ").strip().upper()
        if not my_location:
            print("Операцията е отказана.")
            return
        if my_location not in self.graph.nodes:
            print(f"[!] Локация '{my_location}' не съществува.")
            print(f"Достъпни: {', '.join(self.graph.nodes.keys())}")
            return

        # Взимаме всички складове, които имат продукта
        sources = self.inventory_controller.get_warehouses_with_product(product_name)

        # ако няма никъде наличност
        if not sources:
            print(f"[!] '{product_name}' не е наличен в нито един склад.")
            return

        # превръщаме в чист списък от warehouse_id
        all_sources = []
        for wid, qty in sources:
            wid_up = str(wid).upper()
            all_sources.append(wid_up)

        # Премахваме стартовия склад – търсим най-близкия ДРУГ склад
        other_sources = []
        for s in all_sources:
            if s != my_location:
                other_sources.append(s)

        # ако продуктът е само в стартовия склад
        if not other_sources:
            print(f"[!] '{product_name}' се среща само в {my_location}.")
            return

        # ако продуктът е само в един друг склад
        if len(other_sources) == 1:
            print(f"[*] Продуктът е наличен само в {other_sources[0]}. Изчислявам разстоянието...\n")

        # Стартираме Dijkstra
        distances, predecessors = self.graph.dijkstra(my_location)

        # Филтрираме складовете, до които има път
        reachable = []
        for s in other_sources:
            d = distances.get(s, float('inf'))
            if d < float('inf'):
                reachable.append(s)

        if not reachable:
            print(f"\n[!] Има складове с наличност ({', '.join(other_sources)}), но няма път до тях.")
            return

        # Избираме най-близкия склад
        best_source = reachable[0]
        best_distance = distances[best_source]
        for s in reachable:
            if distances[s] < best_distance:
                best_distance = distances[s]
                best_source = s
        shortest_distance = best_distance

        # Възстановяваме маршрута
        path = []
        step = best_source
        while step is not None:
            path.append(step)
            if step == my_location:
                break
            step = predecessors.get(step)
        path.reverse()

        # Показваме резултата
        source_name = self.graph.nodes[best_source].name

        print("\n" + "═" * 45)
        print("         ЛОГИСТИЧЕН АНАЛИЗ (Dijkstra)")
        print("═" * 45)
        print(f"  Продукт:    {product_name}")
        print(f"  Източник:   {source_name} ({best_source})")
        print(f"  Разстояние: {shortest_distance} км")
        print(f"  Маршрут:    {' -> '.join(path)}")
        print("═" * 45)
        input("\nНатиснете Enter за връщане към менюто...")
