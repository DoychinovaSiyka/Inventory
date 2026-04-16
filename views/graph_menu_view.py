from views.menu import Menu, MenuItem
from graph.warehouse import Warehouse
from graph.warehouse_graph import WarehouseGraph


class GraphView:
    def __init__(self, inventory_controller):
        self.inventory_controller = inventory_controller
        self.graph = WarehouseGraph()
        self._setup_network()  # Създаваме мрежата от складове
        self.menu = self._build_menu()  # Създаваме менюто отделно

    # Създаване на меню
    def _build_menu(self):
        return Menu("Логистичен Модул", [
            MenuItem("1", "Намери най-близка наличност", self.calculate_best_delivery),
            MenuItem("0", "Назад", lambda u: "break")
        ])

    def show_menu(self, user):
        while True:
            choice = self.menu.show()
            if self.menu.execute(choice, user) == "break":
                break

    # Създаване на графа от складове
    def _setup_network(self):
        warehouses = [Warehouse("W1", "София"),
                      Warehouse("W2", "Пловдив"),
                      Warehouse("W3", "Варна"),
                      Warehouse("W4", "Бургас"),
                      Warehouse("W5", "Магазин Смолян")]

        for w in warehouses:
            self.graph.add_warehouse(w)

        # Разстояния
        self.graph.add_edge("W1", "W2", 150)
        self.graph.add_edge("W2", "W4", 250)
        self.graph.add_edge("W4", "W3", 130)
        self.graph.add_edge("W1", "W5", 250)
        self.graph.add_edge("W5", "W3", 350)

    # Намиране на най-близка наличност
    def calculate_best_delivery(self, _):
        product_name = input("Име на стока: ").strip()
        my_location = input("Вашето ID (напр. W1): ").strip()

        if my_location not in self.graph.nodes:
            print("Грешка: Невалидна локация!")
            return

        # Складове, които имат стоката
        possible_sources = self.inventory_controller.get_warehouses_with_product(product_name)
        # Ако продуктът е наличен само в текущия склад
        if possible_sources == [my_location]:
            print(f"\nСтоката '{product_name}' е налична само във вашия склад ({my_location}).")
            print("Няма други складове, от които да се достави.")
            return

        # Изключваме текущия склад – търсим само други
        possible_sources = [s for s in possible_sources if s != my_location]

        if not possible_sources:
            print(f"Стоката '{product_name}' не е налична другаде.")
            return

        # Пускаме Дейкстра от текущия склад
        dist, prev = self.graph.dijkstra(my_location)

        # Намираме най-близкия склад
        best_source = min(possible_sources, key=lambda w: dist[w])
        best_dist = dist[best_source]

        # Възстановяване на маршрута
        path = []
        curr = best_source
        while curr != my_location:
            path.append(curr)
            curr = prev[curr]
        path.append(my_location)
        path.reverse()

        # Показваме резултата
        source_name = self.graph.nodes[best_source].name
        print("\nОПТИМАЛНО РЕШЕНИЕ")
        print(f"Склад: {source_name} ({best_source})")
        print(f"Разстояние: {best_dist} км")
        print(f"Маршрут: {' -> '.join(path)}")
