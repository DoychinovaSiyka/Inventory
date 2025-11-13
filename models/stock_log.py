from datetime import datetime
import uuid
from models.movement import  MovementType


class StockLog(object):
    def __init__(self,product_id,location_id,quantity,action,timestamp = None,log_id = None):
        self.log_id = log_id or str(uuid.uuid4())
        self.product_id = product_id # връзка към Product
        self.location_id = location_id  # връзка към Location
        self.quantity = quantity
        self.action  = action # "delivery" или "sale"
        self.timestamp = timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    def to_dict(self):
        return {
            "log_id": self.log_id,
            "product_id": self.product_id,
            "location_id": self.location_id,
            "quantity": self.quantity,
            "action": self.action,
            "timestamp": self.timestamp
        }


    def deserialize(data):
        return StockLog(
            log_id = data.get("log_id"),
            product_id = data["product_id"],
            location_id = data["location_id"],
            quantity = data["quantity"],
            action = data["action"],
            timestamp = data.get("timestamp")
        )
