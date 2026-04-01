class WarehouseGraph:
    def __init__(self):
        self.nodes = {}  # id -> Warehouse обект
        self.edges = {}  # id -> {neighbor_id: distance}

    def add_warehouse(self, warehouse):
        self.nodes[warehouse.warehouse_id] = warehouse
        if warehouse.warehouse_id not in self.edges:
            self.edges[warehouse.warehouse_id] = {}

    def add_edge(self, from_id, to_id, distance):
        # Добавяме връзката и в двете посоки автоматично
        if from_id in self.nodes and to_id in self.nodes:
            self.edges[from_id][to_id] = distance
            self.edges[to_id][from_id] = distance

# Имам клас Warehouse, който описва един склад чрез ID и име.
# След това имам WarehouseGraph, който представлява граф от складове.
# Всеки склад е възел, а разстоянията между складовете са ребра.
# В nodes пазя всички складове по ID, а в edges пазя съседите и разстоянията до тях.
# add_warehouse добавя нов възел, а add_edge създава двупосочна връзка между два склада.
# Така мога да моделирам логистична мрежа и после да използвам алгоритми като Дейкстра,
# за да намирам най-краткия път между два склада