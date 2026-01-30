from models.location import Location
from validators.location_valiadator import LocationValidator
from datetime import datetime



class LocationController:
    def __init__(self,repo):
        self.repo = repo
        self.locations = [Location.deserialize(l) for l in self.repo.load()]

    def _generate_id(self):
        if not self.locations:
            return 1
        return max(loc.location_id for loc in self.locations) + 1

    def get_all(self):
        return self.locations
    def get_by_id(self,location_id):
        for loc in self.locations:
            if loc.location_id == location_id:
                return loc
        return None

    def exist_by_name(self,name):
        return any(loc.name.lower() ==name.lower() for loc in self.locations)
    def add(self,name,zone = None,capacity = 0):
        # 1) Валидации
        LocationValidator.validate_all(name,zone,capacity)

        # 2) Проверка за дублиране
        if self.exist_by_name(name):
            raise ValueError("Локация с това име вече съществува.")

        # 3)  Създаване на обект
        new_id = self._generate_id()
        now = str(datetime.now())
        location = Location(location_id = new_id, name = name, zone = zone, capacity = capacity,created = now,modified = now)

        # 4) Запис
        self.locations.append(location)
        self._save()

        return location

    def update(self,location_id,name =None,zone =None,capacity =None):
        loc = self.get_by_id(location_id)
        if not loc:
            raise ValueError("Локацията не е намерена.")

        # Валидации
        if name is not None:
            LocationValidator.valide_name(name)
            if self.exist_by_name(name) and name!= loc.name:
                raise ValueError("Локация с това име вече съществува.")
            loc.name = name
        if zone is not None:
            LocationValidator.validate_zone(zone)
            loc.zone = zone
        if capacity is not None:
            LocationValidator.validate_capacity(capacity)
            loc.capacity = zone

        loc.modified = str(datetime.now())
        self._save()

    # DELETE
    def remove(self,location_id):
        loc = self.get_by_id(location_id)
        if not loc:
            return False
        self.locations.remove(loc)
        self._save()
        return True

    # save to JSON
    def _save(self):
        self.repo.save([l.to_dict() for l in self.locations])




# LocationController е важен,защото иначе няма кой да управлява:
# създаване на локации
# списък с локации
# връзка между склад и локация
# евентуално търсене по локация
