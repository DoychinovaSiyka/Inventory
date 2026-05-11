from graph.dijkstra import Graph

class WarehouseGraph(Graph):
    def __init__(self):
        # Инициализирам базовия граф - алгоритмичната структура
        super().__init__(nodes=[], edges=[])

        # Презаписвам nodes и edges, за да пазим реални складове
        self.nodes = {}   # Складове по ID - Warehouse обекти
        self.edges = {}   # Съседни складове и разстояния

    def add_warehouse(self, warehouse):
        # Добавяме в речника на наследника
        wid = warehouse.warehouse_id
        self.nodes[wid] = warehouse

        # базовият клас има структура за ребрата
        if wid not in self.edges:
            self.edges[wid] = {}

    def add_edge(self, from_id, to_id, distance):
        # Добавяне на двупосочна връзка между два склада
        if from_id in self.nodes and to_id in self.nodes:
            self.edges[from_id][to_id] = distance
            self.edges[to_id][from_id] = distance


# WarehouseGraph моделира мрежа от складове като граф.
# Всеки склад е възел, а разстоянията между тях са ребра.
# Това позволява по‑късно да се прилагат алгоритми за намиране на най‑кратък път.
