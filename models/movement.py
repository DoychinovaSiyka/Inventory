from enum import Enum
from datetime import datetime


class MovementType(Enum):
    IN = 0
    OUT = 1
    MOVE = 2



class MetaMovement(type):
    def __new__(cls, *args, **kwargs):
        name = args[0]
        bases = args[1]
        namespace = args[2]

        if 'to_dict' not in namespace:
            def to_dict(self):
                return {
                    "movement_id": self.movement_id,
                    "product_id": self.product_id,
                    "user_id": self.user_id,
                    "location_id": self.location_id,
                    "movement_type": self.movement_type.value,
                    "quantity": self.quantity,
                    "description": self.description,
                    "price":self.price,
                    "data":self.date,
                }
            namespace['to_dict'] = to_dict

        return super().__new__(cls,*args,**kwargs)

class Movement(metaclass=MetaMovement):
    def __init__(self,movement_id,product_id,user_id,location_id,movement_type,quantity,description,price,date = None):

        self.movement_id = movement_id  # int
        self.product_id = product_id   # int
        self.user_id = user_id   # id
        self.location_id = location_id     # id
        self.movement_type = movement_type
        self.quantity = quantity
        self.description = description
        self.price = price
        self.date = date or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    @staticmethod
    def from_dict(data):
        try:
            return Movement(
            movement_id = data["movement_id"],
            product_id = data["product_id"],
            user_id = data["user_id"],
            location_id = data["location_id"],
            movement_type = MovementType(data["movement_type"]),
            quantity = data["quantity"],
            description = data["description"],
            price = data["price"],
            date = data.get("date")
            )
        except KeyError as e:
            print(f"Пропуснат ключ в данните:{e}.")
            return None



