class Warehouse:
    def __init__(self, warehouse_id, name, location="Неизвестна"):
        self.warehouse_id = warehouse_id
        self.name = name
        self.location = location  # Добавяме град или адрес за реализъм

    def __repr__(self):
        # Това е за теб (програмиста), за да виждаш по-ясно обектите в конзолата
        return f"Warehouse(ID: {self.warehouse_id}, Име: {self.name}, Град: {self.location})"