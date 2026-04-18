from datetime import datetime
from typing import Optional, Union


class Location:
    """
    Модел за складова локация.
    Гарантира, че name и zone НИКОГА не са None.
    """

    def __init__(self, location_id: Optional[Union[str, int]] = None,
                 name: Optional[str] = "",
                 zone: Optional[str] = "",
                 capacity: int = 0,
                 created: Optional[str] = None,
                 modified: Optional[str] = None):

        self.location_id = str(location_id) if location_id is not None else None

        # Нормализираме None → ""
        self.name = name if name is not None else ""
        self.zone = zone if zone is not None else ""

        self.capacity = capacity

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        """Сериализация за JSON — гарантира, че няма None."""
        return {
            "location_id": self.location_id,
            "name": self.name or "",
            "zone": self.zone or "",
            "capacity": self.capacity,
            "created": self.created,
            "modified": self.modified
        }

    @staticmethod
    def from_dict(data):
        """Десериализация от JSON — нормализира None → ""."""
        if not data:
            return None

        return Location(
            location_id=data.get("location_id"),
            name=data.get("name") if data.get("name") is not None else "",
            zone=data.get("zone") if data.get("zone") is not None else "",
            capacity=data.get("capacity", 0),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        return f"Локация: {self.name} | Зона: {self.zone} | Капацитет: {self.capacity}"
