import uuid
from datetime import datetime
from typing import Optional, Union

class Location:
    def __init__(self, location_id: Optional[Union[str, int]] = None,
                 name: Optional[str] = "", zone: Optional[str] = "",
                 capacity: int = 0, created: Optional[str] = None, modified: Optional[str] = None):


        if location_id is None:
            self.location_id = str(uuid.uuid4())[:8]
        else:
            self.location_id = str(location_id)

        self.name = name if name is not None else ""
        self.zone = zone if zone is not None else ""
        self.capacity = int(capacity) if capacity is not None else 0

        now_val = Location.now()
        self.created = created or now_val
        self.modified = modified or now_val

    @staticmethod
    def now():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_modified(self):
        """Обновявам датата при промяна на локацията."""
        self.modified = Location.now()

    def to_dict(self):
        """Правя обекта на речник за JSON."""
        return {
            "location_id": self.location_id,
            "name": self.name,
            "zone": self.zone,
            "capacity": self.capacity,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        """Създавам Location от JSON речник."""
        if not data:
            return None

        return Location(
            location_id=data.get("location_id"),
            name=data.get("name"),
            zone=data.get("zone"),
            capacity=data.get("capacity", 0),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        return f"Локация: {self.name} [ID: {self.location_id}] | Зона: {self.zone} | Капацитет: {self.capacity}"