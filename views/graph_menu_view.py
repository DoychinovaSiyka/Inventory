from views.menu import Menu, MenuItem
from graph.warehouse import Warehouse
from graph.warehouse_graph import WarehouseGraph


class GraphView:
    def __init__(self, inventory_controller, location_controller=None):
        self.inventory_controller = inventory_controller
        self.location_controller = location_controller
        self.graph = WarehouseGraph()
        self._setup_network()  # Инициализираме пътната мрежа
        self.menu = self._build_menu()

    def _build_menu(self):
        return Menu("Логистичен Модул (Dijkstra)", [
            MenuItem("1", "Намери най-близка наличност", self.calculate_best_delivery),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def show_menu(self, user):
        while True:
            choice = self.menu.show()
            if choice == "0" or self.menu.execute(choice, user) == "break":
                break

    def _setup_network(self):
        """Дефинираме графа от складове и връзките между тях."""
        warehouses = [
            Warehouse("W1", "София"),
            Warehouse("W2", "Пловдив"),
            Warehouse("W3", "Варна"),
            Warehouse("W4", "Бургас"),
            Warehouse("W5", "Магазин Смолян")
        ]

        for w in warehouses:
            self.graph.add_warehouse(w)

        # Реални пътни разстояния (тегла на ребрата)
        self.graph.add_edge("W1", "W2", 150)
        self.graph.add_edge("W2", "W4", 250)
        self.graph.add_edge("W4", "W3", 130)
        self.graph.add_edge("W1", "W5", 250)
        self.graph.add_edge("W5", "W3", 350)

    def calculate_best_delivery(self, _):
        """ ЛОГИКА НА МОДУЛА:
        Ако продуктът е наличен в стартовия склад - няма доставка.
        Ако продуктът е наличен само в един склад - изчисляваме разстоянието до него.
        Ако продуктът е наличен в няколко склада - Dijkstra намира най-близкия.
        Ако продуктът не е наличен никъде - съобщение.
        Ако няма път между складовете - съобщение."""

        product_name = input("Име на стока: ").strip()
        if not product_name:
            print("[!] Моля, въведете име на стока.")
            return

        my_location = input("Вашето ID (напр. W1): ").strip().upper()

        # Проверка дали началната точка съществува в графа
        if my_location not in self.graph.nodes:
            print(f"\n[!] Грешка: Локация '{my_location}' не съществува в транспортната мрежа!")
            print(f"Достъпни локации: {', '.join(self.graph.nodes.keys())}")
            return

        # Намираме складовете, които имат наличност от продукта
        possible_sources = self.inventory_controller.get_warehouses_with_product(product_name)
        possible_sources = [str(s).upper() for s in possible_sources]

        # Продуктът е наличен в стартовия склад
        if my_location in possible_sources:
            print(f"\n[*] Продуктът '{product_name}' е наличен във вашия склад ({my_location}).")
            print("Няма нужда от доставка.")
            return

        # Продуктът не е наличен в стартовия склад
        print(f"\n[!] Продуктът '{product_name}' не е наличен в {my_location}.")
        print("Търся най-близкия склад с наличност...\n")

        # Филтрираме само складове, които имат наличност
        other_sources = [s for s in possible_sources if s != my_location]

        # Продуктът не е наличен никъде
        if not other_sources:
            print(f"[!] Продуктът '{product_name}' не е намерен в нито един склад.")
            return

        # Продуктът е наличен само в един склад
        if len(other_sources) == 1:
            only_source = other_sources[0]
            print(f"[*] Продуктът е наличен само в един склад: {only_source}.")
            print("Изчислявам разстоянието...\n")

        # Стартираме Dijkstra от стартовия склад
        distances, predecessors = self.graph.dijkstra(my_location)

        # Филтрираме само достижимите складове
        reachable_sources = [s for s in other_sources if distances.get(s, float('inf')) < float('inf')]

        # Има складове с наличност, но няма път до тях
        if not reachable_sources:
            print(f"\n[!] Стоката е налична в {other_sources}, но няма сухопътна връзка до тях.")
            return

        #  Продуктът е наличен в няколко склада - намираме най-близкия
        best_source = min(reachable_sources, key=lambda w: distances[w])
        shortest_distance = distances[best_source]

        # Възстановяваме маршрута
        path = []
        current_step = best_source
        while current_step is not None:
            path.append(current_step)
            if current_step == my_location:
                break
            current_step = predecessors.get(current_step)
        path.reverse()


        source_name = self.graph.nodes[best_source].name
        print("\n" + "═" * 45)
        print("         ЛОГИСТИЧЕН АНАЛИЗ (Dijkstra)")
        print("═" * 45)
        print(f"  Продукт:    {product_name}")
        print(f"  Източник:   {source_name} ({best_source})")
        print(f"  Разстояние: {shortest_distance} км")
        print(f"  Маршрут:    {' ➔ '.join(path)}")
        print("═" * 45)

        input("\nНатиснете Enter за връщане към менюто...")
