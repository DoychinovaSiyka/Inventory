from enum import Enum
from datetime import datetime

class MovementType(Enum):
    DELIVERY = "delivery"
    SALE = "sale"


class Movement:
    def __init__(self,movement_id,product_id,movement_type,quantity,description = "",date = None):
        self.movement_id = movement_id
        self.product_id = product_id
        self.movement_type = movement_type
        self.quantity = quantity
        self.description = description
        self.date = date  or datetime.now().isoformat()


    def to_dict(self):
        return {
            "movement_id": self.movement_id,
            "product_id":  self.product_id,
            "movement_type": self.movement_type.value,
            "description":self.description,
            "date": self.date
        }

    @staticmethod
    def from_dict(data): # #  десериализация превръщам речник (текст) обратно в обект
        return Movement(
            movement_id = data["movement_id"],
            product_id = data["product_id"],
            movement_type = MovementType(data["movement_type"]),
            quantity = data["quantity"],
            description = data.get("description",""),
            date = data.get("date")
        )



