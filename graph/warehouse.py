class Warehouse:

    def __init__(self, warehouse_id, name, location="Неизвестна"):
        self.warehouse_id = warehouse_id
        self.name = name
        self.location = location

    def __repr__(self):
        return f"Warehouse(ID: {self.warehouse_id}, Име: {self.name}, Град: {self.location})"
