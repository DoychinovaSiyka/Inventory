# views/graph_view.py

from menus.menu import Menu, MenuItem
from graph.warehouse import Warehouse
from graph.warehouse_graph import WarehouseGraph
from graph.dijkstra import dijkstra


class GraphView:
    def __init__(self):
        self.graph = WarehouseGraph()

        # Примерни складове
        w1 = Warehouse("W1", "Склад София")
        w2 = Warehouse("W2", "Склад Пловдив")
        w3 = Warehouse("W3", "Склад Варна")
        w4 = Warehouse("W4", "Склад Бургас")

        self.graph.add_warehouse(w1)
        self.graph.add_warehouse(w2)
        self.graph.add_warehouse(w3)
        self.graph.add_warehouse(w4)

        # Примерни разстояния
        self.graph.add_edge("W1", "W2", 150)
        self.graph.add_edge("W2", "W3", 250)
        self.graph.add_edge("W1", "W4", 380)
        self.graph.add_edge("W3", "W4", 90)

    def show_menu(self):
        menu = Menu("Най-кратък път между складове (Dijkstra)", [
            MenuItem("1", "Изчисли най-кратък път", self.calculate_path),
            MenuItem("0", "Назад", lambda u: "break")
        ])

        while True:
            choice = menu.show()
            result = menu.execute(choice, None)
            if result == "break":
                break

    def calculate_path(self, user):
        print("\nНалични складове:")
        for wid, w in self.graph.nodes.items():
            print(f"{wid}: {w.name}")

        start = input("Начален склад (ID): ").strip()
        end = input("Краен склад (ID): ").strip()

        try:
            distance, path = dijkstra(self.graph, start, end)
            print("\n=== Резултат ===")
            print("Маршрут:", " → ".join(path))
            print("Общо разстояние:", distance, "км")
        except Exception as e:
            print("Грешка:", e)
