from enum import Enum
from datetime import datetime
import uuid
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
                    "price":self.price,
                    "created": self.created,
                    "modified": self.modified
                }
            namespace['to_dict'] = to_dict

        return super().__new__(cls,*args,**kwargs)

class Movement(metaclass=MetaMovement):
    def __init__(self,product_id,movement_type,quantity,description,price,created=None,modified=None,movement_id = None):
        if movement_id is not None:
            self.movement_id = movement_id
        else:
            self.movement_id = str(uuid.uuid4())

        self.product_id = product_id
        self.movement_type = movement_type
        self.quantity = quantity
        self.description = description
        self.price = price
        if created is not None:
            self.created = created
        else:
            self.created = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if modified is not None:
            self.modified = modified
        else:
            self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    @staticmethod
    def from_dict(data):
        try:
            return Movement(
            movement_id = data.get("movement_id"),
            product_id = data.get("product_id"),
            movement_type = MovementType(data["movement_type"]),
            quantity = data["quantity"],
            description = data["description"],
            price = data["price"],
            created= data["created"],
            modified = data["modified"])
        except KeyError as e:
            print(f"Пропуснат ключ в данните:{e}.")
            return None







