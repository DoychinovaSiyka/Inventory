class WarehouseGraph:
    def __init__(self):
        self.nodes = {}      # warehouse_id -> Warehouse
        self.edges = {}      # warehouse_id -> {neighbor_id: distance}

    def add_warehouse(self, warehouse):
        self.nodes[warehouse.warehouse_id] = warehouse
        self.edges[warehouse.warehouse_id] = {}

    def add_edge(self, from_id, to_id, distance):
        if from_id not in self.nodes or to_id not in self.nodes:
            raise ValueError("Невалиден warehouse_id")

        self.edges[from_id][to_id] = distance
        self.edges[to_id][from_id] = distance  # двупосочно
