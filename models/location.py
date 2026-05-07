import uuid
from datetime import datetime
from typing import Optional, Union


class Location:
    def __init__(self, location_id: Optional[Union[str, int]] = None,
                 name: Optional[str] = "", zone: Optional[str] = "",
                 capacity: int = 0, created: Optional[str] = None,
                 modified: Optional[str] = None):

        # ID
        if location_id is None:
            self.location_id = str(uuid.uuid4())
        else:
            self.location_id = str(location_id)

        # Име
        if name is not None:
            self.name = name
        else:
            self.name = ""

        # Зона
        if zone is not None:
            self.zone = zone
        else:
            self.zone = ""

        # Капацитет
        if capacity is not None:
            self.capacity = int(capacity)
        else:
            self.capacity = 0

        # Дати
        now_val = Location.now()

        if created:
            self.created = created
        else:
            self.created = now_val

        if modified:
            self.modified = modified
        else:
            self.modified = now_val

    @staticmethod
    def now():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def update_modified(self):
        """Обновявам датата при промяна на локацията."""
        self.modified = Location.now()

    def to_dict(self):
        """Записваме в JSON пълното 36-символно ID."""
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
        short_id = self.location_id[:8]
        return f"Локация: {self.name} [ID: {short_id}] | Зона: {self.zone} | Капацитет: {self.capacity}"
