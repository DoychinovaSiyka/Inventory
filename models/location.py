from datetime import datetime
from typing import Optional, Union


class Location:
    # Анотацията на location_id да бъде Union[str, int, None],
    # но в логиката ще го превръщаме в str за консистентност с "W1", "W2"...
    def __init__(self, location_id: Optional[Union[str, int]] = None, name: str = "",
                 zone: str = "", capacity: int = 0,
                 created: Optional[str] = None, modified: Optional[str] = None):

        # ID-то винаги е текст ако не е None
        self.location_id = str(location_id) if location_id is not None else None

        self.name = name
        self.zone = zone
        self.capacity = capacity

        # Дати
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        """Обновява датата на последна промяна."""
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        """Сериализация за JSON."""
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
        """Десериализация от JSON."""
        if not data:
            return None

        # При зареждане от JSON, ако случайно ID-то е число,
        # конструкторът ще го превърне в "1", "2" и т.н.
        return Location(
            location_id=data.get("location_id"),
            name=data.get("name", ""),
            zone=data.get("zone", ""),
            capacity=data.get("capacity", 0),
            created=data.get("created"),
            modified=data.get("modified")
        )

    def __str__(self):
        return f"Локация: {self.name} | Зона: {self.zone} | Капацитет: {self.capacity}"
