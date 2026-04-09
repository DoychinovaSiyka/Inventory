from typing import Optional, List
from datetime import datetime
from models.location import Location
from storage.json_repository import JSONRepository


class LocationController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        # Зареждаме локациите
        self.locations: List[Location] = [Location.from_dict(l) for l in self.repo.load()]

    # ID GENERATOR - поддържам консистентност с "W" префикса
    def _generate_id(self) -> str:
        if not self.locations:
            return "W1"
        try:
            ids = []
            for l in self.locations:
                # Вземам числото след 'W'
                num_part = str(l.location_id).replace("W", "")
                if num_part.isdigit():
                    ids.append(int(num_part))

            next_id = max(ids) + 1 if ids else 1
            return f"W{next_id}"

        except:
            # Ако по не са във формат W1, генерираме по стария начин, но като стринг
            return str(len(self.locations) + 1)


    # CREATE
    def add(self, name: str, zone: str = "", capacity: int = 0) -> Location:
        if not name or len(name.strip()) == 0:
            raise ValueError("Името на локацията е задължително.")

        if capacity < 0:
            raise ValueError("Капацитетът трябва да бъде >= 0.")

        if any(l.name.lower() == name.lower() for l in self.locations):
            raise ValueError("Локация с това име вече съществува.")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Генерираме ID от типа "W1", "W2"...
        location = Location(location_id=self._generate_id(), name=name, zone=zone, capacity=capacity,
                            created=now, modified=now)
        self.locations.append(location)
        self.save_changes()
        return location

    # READ
    def get_all(self) -> List[Location]:
        return self.locations

    # Търсим по стринг (W1), защото така са в графа
    def get_by_id(self, location_id: str) -> Optional[Location]:
        return next((l for l in self.locations if str(l.location_id) == str(location_id)),None)

    # UPDATE
    def update(self, location_id: str, name: Optional[str] = None,
               zone: Optional[str] = None, capacity: Optional[int] = None) -> bool:
        location = self.get_by_id(location_id)
        if not location:
            raise ValueError("Локацията не е намерена.")

        if name is not None:
            if len(name.strip()) == 0:
                raise ValueError("Името не може да бъде празно.")
            if any(l.name.lower() == name.lower() and l.location_id != location_id for l in self.locations):
                raise ValueError("Локация с това име вече съществува.")
            location.name = name
        if zone is not None:
            location.zone = zone
        if capacity is not None:
            if capacity < 0:
                raise ValueError("Капацитетът трябва да бъде >= 0.")
            location.capacity = capacity
        location.update_modified()
        self.save_changes()
        return True


    def remove(self, location_id: str) -> bool:
        original_len = len(self.locations)

        self.locations = [ l for l in self.locations if str(l.location_id) != str(location_id)]
        if len(self.locations) < original_len:
            self.save_changes()
            return True
        return False

    def save_changes(self) -> None:
        self.repo.save([l.to_dict() for l in self.locations])
