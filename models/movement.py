from enum import Enum
from datetime import datetime

class MovementType(Enum):
    DELIVERY = "delivery"
    SALE = "sale"



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
                    "movement_type": self.movement_type.value,
                    "quantity": self.quantity,
                    "description": self.description,
                    "date": self.date
                }
            namespace['to_dict'] = to_dict

        return super().__new__(cls,*args,**kwargs)

class Movement(metaclass=MetaMovement):
    def __init__(self,movement_id,product_id,movement_type,quantity,description = "",date = None):
        self.movement_id = movement_id
        self.product_id = product_id
        self.movement_type = movement_type
        self.quantity = quantity
        self.description = description
        self.date = date  or datetime.now().isoformat()




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

    def __str__(self):
        return f"[{self.movement_type.name}] {self.quantity} бр. за продукт {self.product_id} на {self.date}"



m1 = Movement(
    movement_id=1,
    product_id=101,
    movement_type=MovementType.DELIVERY,
    quantity=50,
    description="Първоначална доставка"
)
print(m1)
print(m1.to_dict())



