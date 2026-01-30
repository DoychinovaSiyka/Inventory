from graph.warehouse import Warehouse
from graph.warehouse_graph import WarehouseGraph
from graph.dijkstra import dijkstra


def graph_menu():
    graph = WarehouseGraph()

    # Примерни складове (можеш да ги зареждаш и от JSON ако искаш)
    w1 = Warehouse("W1", "Склад София")
    w2 = Warehouse("W2", "Склад Пловдив")
    w3 = Warehouse("W3", "Склад Варна")
    w4 = Warehouse("W4", "Склад Бургас")

    graph.add_warehouse(w1)
    graph.add_warehouse(w2)
    graph.add_warehouse(w3)
    graph.add_warehouse(w4)

    # Примерни разстояния
    graph.add_edge("W1", "W2", 150)
    graph.add_edge("W2", "W3", 250)
    graph.add_edge("W1", "W4", 380)
    graph.add_edge("W3", "W4", 90)

    while True:
        print("\n=== Най-кратък път между складове (Dijkstra) ===")
        print("1. Изчисли най-кратък път")
        print("0. Назад")

        choice = input("Избор: ")

        if choice == "1":
            print("\nНалични складове:")
            for wid, w in graph.nodes.items():
                print(f"{wid}: {w.name}")

            start = input("Начален склад (ID): ").strip()
            end = input("Краен склад (ID): ").strip()

            try:
                distance, path = dijkstra(graph, start, end)
                print("\n=== Резултат ===")
                print("Маршрут:", " → ".join(path))
                print("Общо разстояние:", distance, "км")
            except Exception as e:
                print("Грешка:", e)

        elif choice == "0":
            break

        else:
            print("Невалиден избор.")
