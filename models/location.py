


class Location:
    def __init__(self,location_id = None,name = "",zone = "",capacity = 0,city = ""):
        self.location_id = location_id
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
    def from_dict(data):
        return Location(
            location_id = data["location_id"],
            name = data.get("name",""),
            zone = data.get("zone",""),
            capacity = data.get("capacity",0),
            city = data.get("city","")
        )

