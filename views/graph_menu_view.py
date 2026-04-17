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
        # Важно: ID-тата трябва да съвпадат точно с тези в inventory.json (W1, W2...)
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
        self.graph.add_edge("W1", "W2", 150)  # София - Пловдив
        self.graph.add_edge("W2", "W4", 250)  # Пловдив - Бургас
        self.graph.add_edge("W4", "W3", 130)  # Бургас - Варна
        self.graph.add_edge("W1", "W5", 250)  # София - Смолян
        self.graph.add_edge("W5", "W3", 350)  # Смолян - Варна

    def calculate_best_delivery(self, _):
        """Изчислява най-краткия път до склад, който има търсената стока."""
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

        #  Намираме складовете, които имат наличност от продукта
        # Този метод вече е оправихме в InventoryController да ползва self.data
        possible_sources = self.inventory_controller.get_warehouses_with_product(product_name)

        # Филтрираме текущия склад (не ни трябва път до нас самите)
        other_sources = [s for s in possible_sources if str(s).upper() != my_location]

        if not other_sources:
            # Проверяваме дали изобщо има такава стока някъде
            if my_location in [str(s).upper() for s in possible_sources]:
                print(f"\n[*] Продуктът '{product_name}' е наличен само при вас ({my_location}).")
            else:
                print(f"\n[!] Продуктът '{product_name}' не е намерен в нито един склад.")
            return

        # Изпълняваме алгоритъма на Дейкстра от нашата локация
        distances, predecessors = self.graph.dijkstra(my_location)

        #  Филтрираме само тези складове със стока, до които реално има път
        reachable_sources = [s for s in other_sources if distances.get(s, float('inf')) < float('inf')]

        if not reachable_sources:
            print(f"\n[!] Стоката е налична в {other_sources}, но няма сухопътна връзка до тях.")
            return

        # Избираме източника с най-малко разстояние
        best_source = min(reachable_sources, key=lambda w: distances[w])
        shortest_distance = distances[best_source]

        # Възстановяваме маршрута стъпка по стъпка
        path = []
        current_step = best_source
        try:
            while current_step is not None:
                path.append(current_step)
                if current_step == my_location:
                    break
                current_step = predecessors.get(current_step)
            path.reverse()
        except Exception:
            print("\n[!] Възникна грешка при генерирането на маршрута.")
            return

        # Визуализация на резултата
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