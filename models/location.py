import uuid
from datetime import datetime
from typing import Optional, Union


class Location:
    def __init__(self, location_id: Optional[Union[str, int]] = None, name: Optional[str] = "",
                 zone: Optional[str] = "", capacity: int = 0, created: Optional[str] = None,
                 modified: Optional[str] = None, code: Optional[str] = None  ):


        self.location_id = str(location_id) if location_id else str(uuid.uuid4())
        self.name = name if name is not None else ""
        self.zone = zone if zone is not None else ""
        self.capacity = int(capacity) if capacity is not None else 0

        # Код за Dijkstra (W1, W2, W3...)
        self.code = code if code is not None else ""

        now_val = Location.now()
        self.created = created if created else now_val
        self.modified = modified if modified else now_val



    @staticmethod
    def now():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_modified(self):
        self.modified = Location.now()

    def to_dict(self):
        return {"location_id": self.location_id, "name": self.name, "zone": self.zone,
                "capacity": self.capacity, "created": self.created,
                "modified": self.modified, "code": self.code}


    @staticmethod
    def from_dict(data):
        if not data:
            return None

        return Location(location_id=data.get("location_id"), name=data.get("name"),
                        zone=data.get("zone"), capacity=data.get("capacity", 0),
                        created=data.get("created"), modified=data.get("modified"), code=data.get("code"))


    def __str__(self):
        short_id = self.location_id[:8]
        return f"Локация: {self.name} [ID: {short_id}] | Код: {self.code} | Зона: {self.zone} | Капацитет: {self.capacity}"
