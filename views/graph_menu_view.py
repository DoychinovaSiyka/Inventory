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

    def _setup_network(self):  # настройвам си складовете и разстоянията между тях
        """Създавам складовете и задавам примерни разстояния. Това е графът, върху който
        работи Dijkstra."""
        warehouses = [Warehouse("W1", "София"),
                      Warehouse("W2", "Пловдив"), Warehouse("W3", "Варна"),
                      Warehouse("W4", "Бургас"), Warehouse("W5", "Магазин Смолян")]

        # добавям всички складове в графа
        for w in warehouses:
            self.graph.add_warehouse(w)

        # разстояния между складовете – примерни, но реалистични
        self.graph.add_edge("W1", "W2", 150)
        self.graph.add_edge("W2", "W4", 250)
        self.graph.add_edge("W4", "W3", 130)
        self.graph.add_edge("W1", "W5", 250)
        self.graph.add_edge("W5", "W3", 350)

    def _build_menu(self):
        # Създаваме менюто за логистичния модул
        # Менюто съдържа основната функция – търсене на най-близък склад
        return Menu("Логистичен Модул (Dijkstra)", [
            MenuItem("1", "Намери най-близка наличност", self.calculate_best_delivery),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def show_menu(self, user: User):
        while True:
            # Изграждаме менюто динамично за по-голяма гъвкавост
            menu = self._build_menu()
            choice = menu.show()

            if menu.execute(choice, user) == "break":
                break

    def calculate_best_delivery(self, user: User):  # основната логика за намиране на най-близкия склад
        """Проверявам дали продуктът е в стартовия склад. Ако не е – търся всички складове
        с наличност и Dijkstra избира най-близкия."""

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

        # взимам всички складове, които имат този продукт
        possible_sources = self.inventory_controller.get_warehouses_with_product(product_name)
        possible_sources = [str(s).upper() for s in possible_sources]

        # ако продуктът е в стартовия склад - няма доставка
        if my_location in possible_sources:
            print(f"\n[*] '{product_name}' е наличен в {my_location}. Няма нужда от доставка.")
            return

        print(f"\n[!] '{product_name}' не е наличен в {my_location}. Търся най-близкия склад...\n")

        # всички складове с наличност, различни от стартовия
        other_sources = [s for s in possible_sources if s != my_location]
        if not other_sources:
            print(f"[!] '{product_name}' не е намерен в нито един склад.")
            return

        if len(other_sources) == 1:
            print(f"[*] Продуктът е само в {other_sources[0]}. Изчислявам разстоянието...\n")

        # стартирам Dijkstra
        distances, predecessors = self.graph.dijkstra(my_location)

        # филтрирам складовете, до които реално има път
        reachable_sources = [s for s in other_sources if distances.get(s, float('inf')) < float('inf')]

        if not reachable_sources:
            print(f"\n[!] Има складове с наличност ({', '.join(other_sources)}), но няма път до тях.")
            return

        # най-близкият склад
        best_source = min(reachable_sources, key=lambda w: distances[w])
        shortest_distance = distances[best_source]

        # възстановявам маршрута
        path, current_step = [], best_source
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