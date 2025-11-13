

import uuid

class Location:
    def __init__(self,location_id = None,name = "",zone = "",capacity = 0,city = ""):
        self.location_id = location_id if location_id else str(uuid.uuid4())
        self.name = name
        self.zone = zone
        self.capacity = capacity
        self.city = city

    def to_dict(self):
        return{
            "location_id":self.location_id,
            "name": self.name,
            "zone": self.zone,
            "capacity": self.capacity,
            "city": self.city
        }
    @staticmethod
    def deserialize(data):
        return Location(
            location_id = data.get("location_id"),
            name = data.get("name"),
            zone = data.get("zone"),
            capacity = data.get("capacity"),
            city = data.get("city")
        )

