import uuid
from datetime import datetime
from typing import Optional, Union





class Location:
    def __init__(self, location_id: Optional[Union[str, int]] = None,
                 name: Optional[str] = "", zone: Optional[str] = "",
                 capacity: int = 0, created: Optional[str] = None, modified: Optional[str] = None, code: Optional[str] = None):


        if location_id is not None:
            self.location_id = str(location_id)
        else:
            self.location_id = str(uuid.uuid4())


        if name is not None:
            self.name = name
        else:
            self.name = ""


        if zone is not None:
            self.zone = zone
        else:
            self.zone = ""


        if capacity is not None:
            self.capacity = int(capacity)
        else:
            self.capacity = 0

        # Код за Dijkstra (W1, W2, W3...)
        if code is not None:
            self.code = code
        else:
            self.code = ""


        now_val = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if isinstance(created, str):
            self.created = created
        else:
            self.created = now_val

        if isinstance(modified, str):
            self.modified = modified
        else:
            self.modified = now_val




    def update_modified(self):
        self.modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    def to_dict(self):
        return {"location_id": self.location_id, "name": self.name, "zone": self.zone,
                "capacity": self.capacity, "created": self.created,
                "modified": self.modified, "code": self.code}




    @staticmethod
    def from_dict(data):
        if not data:
            return None

        return Location(location_id=data.get("location_id"), name=data.get("name"), zone=data.get("zone"),
                        capacity=data.get("capacity", 0), created=data.get("created"),
                        modified=data.get("modified"), code=data.get("code"))



    def __str__(self):
        short_id = self.location_id[:8]
        return f"Локация: {self.name} [ID: {short_id}] | Код: {self.code} | Зона: {self.zone} | Капацитет: {self.capacity}"
