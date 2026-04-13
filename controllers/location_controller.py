from typing import Optional, List
from datetime import datetime
from models.location import Location
from storage.json_repository import JSONRepository
from validators.location_validator import LocationValidator


class LocationController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        # Зареждам всички локации от JSON и ги преобразувам в Location обекти
        self.locations: List[Location] = [Location.from_dict(l) for l in self.repo.load()]

    # ID GENERATOR - поддържам консистентност с "W" префикса
    def _generate_id(self) -> str:
        if not self.locations:
            return "W1"

        ids = []
        for l in self.locations:
            num_part = str(l.location_id).replace("W", "")
            if num_part.isdigit():
                ids.append(int(num_part))

        next_id = max(ids) + 1 if ids else 1
        return f"W{next_id}"

    # CREATE
    def add(self, name: str, zone: str = "", capacity=None) -> Location:
        # Валидации
        name = LocationValidator.validate_name(name)
        zone = LocationValidator.validate_zone(zone)
        capacity = LocationValidator.validate_capacity(capacity)

        # Проверка за дублиране
        for l in self.locations:
            if l.name.lower() == name.lower():
                raise ValueError("Локация с това име вече съществува.")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        location = Location(
            location_id=self._generate_id(),
            name=name,
            zone=zone,
            capacity=capacity,
            created=now,
            modified=now
        )

        self.locations.append(location)
        self.save_changes()
        return location

    # READ
    def get_all(self) -> List[Location]:
        return self.locations

    def get_by_id(self, location_id: str) -> Location:
        # Търсим локацията по най‑ясния и човешки начин
        for loc in self.locations:
            if str(loc.location_id) == str(location_id):
                return loc

        # Ако не е намерена → хвърляме грешка
        raise ValueError(f"Локация с код '{location_id}' не съществува.")

    # UPDATE
    def update(self, location_id: str, name: Optional[str] = None,
               zone: Optional[str] = None, capacity=None) -> bool:

        location = self.get_by_id(location_id)

        # Ако полето е None → значи View не иска да го променя
        if name is not None:
            name = LocationValidator.validate_name(name)
            # Проверка за дублиране
            for l in self.locations:
                if l.name.lower() == name.lower() and l.location_id != location_id:
                    raise ValueError("Локация с това име вече съществува.")
            location.name = name

        if zone is not None:
            zone = LocationValidator.validate_zone(zone)
            location.zone = zone

        if capacity is not None:
            capacity = LocationValidator.validate_capacity(capacity)
            location.capacity = capacity

        location.update_modified()
        self.save_changes()
        return True

    # DELETE
    def remove(self, location_id: str) -> bool:
        location = self.get_by_id(location_id)
        # Премахване
        self.locations = [l for l in self.locations if l.location_id != location_id]
        self.save_changes()
        return True

    # SAVE
    def save_changes(self) -> None:
        self.repo.save([l.to_dict() for l in self.locations])
