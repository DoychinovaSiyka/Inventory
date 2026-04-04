from views.menu import Menu, MenuItem
from graph.warehouse import Warehouse
from graph.warehouse_graph import WarehouseGraph
from graph.dijkstra import dijkstra


class GraphView:
    def __init__(self, inventory_controller):
        self.inventory_controller = inventory_controller
        self.graph = WarehouseGraph()

        # Създаваме мрежата от складове
        self._setup_network()

        # Създаваме менюто отделно (мега ООП)
        self.menu = self._build_menu()

    # Създаване на меню
    def _build_menu(self):
        return Menu("Логистичен Модул", [
            MenuItem("1", "Намери най-близка наличност", self.calculate_best_delivery),
            MenuItem("0", "Назад", lambda u: "break") ])


    # Основно меню
    def show_menu(self, user):
        while True:
            choice = self.menu.show()
            if self.menu.execute(choice, user) == "break":
                break


    # Създаване на графа от складове
    def _setup_network(self):
        warehouses = [ Warehouse("W1", "София"), Warehouse("W2", "Пловдив"),
                       Warehouse("W3", "Варна"), Warehouse("W4", "Бургас"),
                       Warehouse("W5", "Русе")]
        for w in warehouses:
            self.graph.add_warehouse(w)

        # Добавяме пътища между складовете
        self.graph.add_edge("W1", "W2", 150)
        self.graph.add_edge("W2", "W4", 250)
        self.graph.add_edge("W4", "W3", 130)
        self.graph.add_edge("W1", "W5", 310)
        self.graph.add_edge("W5", "W3", 190)


    # Намиране на най-близка наличност
    def calculate_best_delivery(self, _):
        product_name = input("Име на стока: ").strip()
        my_location = input("Вашето ID (напр. W1): ").strip()

        if my_location not in self.graph.nodes:
            print("Грешка: Невалидна локация!")
            return

        # Намираме складовете, в които има наличност
        possible_sources = self.inventory_controller.get_warehouses_with_product(product_name)
        possible_sources = [s for s in possible_sources if s != my_location]

        if not possible_sources:
            print(f"Стоката '{product_name}' не е налична другаде.")
            return

        best_dist = float('inf')
        best_path = []
        best_source = None

        # Търсим най-краткия път с Dijkstra
        for source_id in possible_sources:
            dist, path = dijkstra(self.graph, source_id, my_location)
            if dist < best_dist:
                best_dist = dist
                best_path = path
                best_source = source_id

        # Показваме резултата
        if best_source:
            source_name = self.graph.nodes[best_source].name
            print("\nОПТИМАЛНО РЕШЕНИЕ")
            print(f"Склад: {source_name} ({best_source})")
            print(f"Разстояние: {best_dist} км")
            print(f"Маршрут: {' -> '.join(best_path)}")
        else:
            print("Няма открит маршрут.")
