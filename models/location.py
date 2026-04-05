from datetime import datetime
from typing import Optional, Union


class Location:
    # Променяме анотацията на location_id да бъде Union[str, int, None],
    # но в логиката ще го превръщаме в str за консистентност с "W1", "W2"...
    def __init__(self, location_id: Optional[str] = None, name: str = "",
                 zone: str = "", capacity: int = 0,
                 created: Optional[str] = None, modified: Optional[str] = None):
        # Уверяваме се, че ID-то винаги е текст (ако не е None)
        self.location_id = str(location_id) if location_id is not None else None
        self.name = name
        self.zone = zone
        self.capacity = capacity

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
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
        # При зареждане от JSON, ако случайно ID-то е число,
        # конструкторът ни горе ще го превърне в "1", "2" и т.н.
        return Location(location_id=data.get("location_id"), name=data.get("name", ""),
                        zone=data.get("zone", ""), capacity=data.get("capacity", 0),
                        created=data.get("created"), modified=data.get("modified"))
