class Warehouse:
    def __init__(self, warehouse_id, name):
        self.warehouse_id = warehouse_id
        self.name = name

    def __repr__(self):
        return f"Warehouse({self.warehouse_id}, {self.name})"
