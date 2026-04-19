from views.menu import Menu, MenuItem
from graph.warehouse import Warehouse
from graph.warehouse_graph import WarehouseGraph


class GraphView:
    def __init__(self, inventory_controller, location_controller=None):
        self.inventory_controller = inventory_controller
        self.location_controller = location_controller
        self.graph = WarehouseGraph()

        # Подготвяме мрежата от складове и разстоянията между тях
        self._setup_network()

        # Създаваме менюто за логистичния модул
        self.menu = self._build_menu()

    def _build_menu(self):
        # Менюто съдържа основната функция – търсене на най-близък склад
        return Menu("Логистичен Модул (Dijkstra)", [
            MenuItem("1", "Намери най-близка наличност", self.calculate_best_delivery),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def show_menu(self, user):
        # Обикновен цикъл за работа с менюто
        while True:
            choice = self.menu.show()
            if choice == "0" or self.menu.execute(choice, user) == "break":
                break

    def _setup_network(self):
        """Създаваме складовете и задаваме разстоянията между тях.
        Това е нашият граф, върху който работи Dijkstra.
        """
        warehouses = [
            Warehouse("W1", "София"),
            Warehouse("W2", "Пловдив"),
            Warehouse("W3", "Варна"),
            Warehouse("W4", "Бургас"),
            Warehouse("W5", "Магазин Смолян")
        ]

        # Добавяме всички складове в графа
        for w in warehouses:
            self.graph.add_warehouse(w)

        # Разстояния между складовете (в километри)
        # Тези стойности са примерни, но реалистични
        self.graph.add_edge("W1", "W2", 150)
        self.graph.add_edge("W2", "W4", 250)
        self.graph.add_edge("W4", "W3", 130)
        self.graph.add_edge("W1", "W5", 250)
        self.graph.add_edge("W5", "W3", 350)

    def calculate_best_delivery(self, _):
        """Основната логика:
        - Проверяваме дали продуктът е наличен в стартовия склад.
        - Ако не е, търсим всички складове, които го имат.
        - Ако има няколко – Dijkstra намира най-близкия.
        - Ако няма път – информираме потребителя.
        """

        product_name = input("Име на стока: ").strip()
        if not product_name:
            print("[!] Моля, въведете име на стока.")
            return

        my_location = input("Вашето ID (напр. W1): ").strip().upper()

        # Проверяваме дали въведеният склад съществува в графа
        if my_location not in self.graph.nodes:
            print(f"\n[!] Локация '{my_location}' не съществува в транспортната мрежа.")
            print(f"Достъпни локации: {', '.join(self.graph.nodes.keys())}")
            return

        # Взимаме всички складове, които имат наличност от продукта
        possible_sources = self.inventory_controller.get_warehouses_with_product(product_name)
        possible_sources = [str(s).upper() for s in possible_sources]

        # Ако продуктът е наличен в стартовия склад – няма нужда от доставка
        if my_location in possible_sources:
            print(f"\n[*] Продуктът '{product_name}' е наличен във вашия склад ({my_location}).")
            print("Няма нужда от доставка.")
            return

        print(f"\n[!] Продуктът '{product_name}' не е наличен в {my_location}.")
        print("Търся най-близкия склад...\n")

        # Всички складове, които имат наличност, различни от стартовия
        other_sources = [s for s in possible_sources if s != my_location]

        # Ако никой склад не го предлага
        if not other_sources:
            print(f"[!] Продуктът '{product_name}' не е намерен в нито един склад.")
            return

        # Ако има само един склад с наличност – директно ще го проверим
        if len(other_sources) == 1:
            print(f"[*] Продуктът е наличен само в един склад: {other_sources[0]}.")
            print("Изчислявам разстоянието...\n")

        # Стартираме Dijkstra от стартовия склад
        distances, predecessors = self.graph.dijkstra(my_location)

        # Филтрираме складовете, до които реално има път
        reachable_sources = [
            s for s in other_sources
            if distances.get(s, float('inf')) < float('inf')
        ]

        # Ако има складове с наличност, но няма път до тях
        if not reachable_sources:
            print(f"\n[!] Има складове с наличност ({other_sources}), но няма път до тях.")
            return

        # Избираме най-близкия склад според Dijkstra
        best_source = min(reachable_sources, key=lambda w: distances[w])
        shortest_distance = distances[best_source]

        # Възстановяваме маршрута от Dijkstra
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
