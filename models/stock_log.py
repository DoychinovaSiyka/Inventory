class StockLog:
    def __init__(self, product_id, location_id, quantity, unit, action, timestamp, log_id=None):
        """ Модел за лог запис. timestamp се подава винаги отвън (Controller), за да има синхрон."""
        # ID-то идва от контролера (или JSON)
        self.log_id = str(log_id) if log_id else None
        self.product_id = str(product_id)
        self.location_id = str(location_id)
        self.quantity = float(quantity)
        self.unit = str(unit).strip()
        self.action = str(action).lower()
        # Датата винаги идва отвън
        self.timestamp = timestamp

    def to_dict(self):
        """Превръща обекта в речник за JSON съхранение."""
        return {
            "log_id": self.log_id,
            "product_id": self.product_id,
            "location_id": self.location_id,
            "quantity": self.quantity,
            "unit": self.unit,
            "action": self.action,
            "timestamp": self.timestamp
        }

    @staticmethod
    def from_dict(data):
        """Възстановява обекта от речник (JSON)."""
        if not data:
            return None

        return StockLog(
            log_id=data.get("log_id"),
            product_id=data.get("product_id"),
            location_id=data.get("location_id"),
            quantity=data.get("quantity"),
            unit=data.get("unit", "бр."),
            action=data.get("action"),
            timestamp=data.get("timestamp")
        )

    def __str__(self):
        return f"[{self.timestamp}] {self.action.upper()} | {self.product_id} @ {self.location_id} | {self.quantity} {self.unit}"
