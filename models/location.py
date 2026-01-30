from datetime import datetime

class Location:
    def __init__(self, location_id=None, name="", zone="", capacity=0, created=None, modified=None):
        self.location_id = location_id
        self.name = name
        self.zone = zone
        self.capacity = capacity
        self.created = created or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.modified = modified or datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
        return Location(
            location_id=data.get("location_id"),
            name=data.get("name", ""),
            zone=data.get("zone", ""),
            capacity=data.get("capacity", 0),
            created=data.get("created"),
            modified=data.get("modified")
        )
