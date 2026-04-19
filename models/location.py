from datetime import datetime
from typing import Optional, Union


class Location:
    """
    Модел за складова локация.
    Поддържа name и zone винаги като текст, без None.
    """

    def __init__(self, location_id: Optional[Union[str, int]] = None,
                 name: Optional[str] = "",
                 zone: Optional[str] = "",
                 capacity: int = 0,
                 created: Optional[str] = None,
                 modified: Optional[str] = None):

        # ID-то може да е число или текст, но го държим като стринг
        self.location_id = str(location_id) if location_id is not None else None

        # Ако от JSON дойде None → превръщаме го в празен стринг
        self.name = name if name is not None else ""
        self.zone = zone if zone is not None else ""

        self.capacity = capacity

        # Дати на създаване и последна промяна
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.created = created or now
        self.modified = modified or now

    def update_modified(self):
        """Обновява датата при промяна на локацията."""
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        """Подготвя обекта за запис в JSON."""
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
        """Създава Location от JSON речник и нормализира празните стойности."""
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
