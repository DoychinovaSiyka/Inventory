import uuid
from datetime import datetime

class StockLog:
    def __init__(self, product_id, location_id, quantity, unit, action, timestamp=None, log_id=None):
        self.log_id = log_id or str(uuid.uuid4())
        self.product_id = product_id
        self.location_id = location_id
        self.quantity = quantity
        self.unit = unit                  # ← НОВО
        self.action = action              # add, remove, move
        self.timestamp = timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "product_id": self.product_id,
            "location_id": self.location_id,
            "quantity": self.quantity,
            "unit": self.unit,            # ← НОВО
            "action": self.action,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data):
        return StockLog(
            log_id=data.get("log_id"),
            product_id=data["product_id"],
            location_id=data["location_id"],
            quantity=data["quantity"],
            unit=data.get("unit", "бр."),   # ← НОВО (fallback ако липсва)
            action=data["action"],
            timestamp=data.get("timestamp")
        )
