from typing import Optional, List
from datetime import datetime
from models.location import Location
from storage.json_repository import JSONRepository


class LocationController:
    def __init__(self, repo: JSONRepository):
        self.repo = repo
        self.locations: List[Location] = [Location.from_dict(l) for l in self.repo.load()]
        # Зареждаме всички локации от JSON файла чрез хранилището.
        # Location.from_dict преобразува речниците в реални Location обекти.

    # ID GENERATOR
    def _generate_id(self) -> int:
        if not self.locations:
            return 1
        return max(l.location_id for l in self.locations) + 1

    # CREATE
    def add(self, name: str, zone: str = "", capacity: int = 0) -> Location:
        if not name or len(name.strip()) == 0:
            raise ValueError("Името на локацията е задължително.")

        if capacity < 0:
            raise ValueError("Капацитетът трябва да бъде >= 0.")

        # Проверка за дублиране
        if any(l.name.lower() == name.lower() for l in self.locations):
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
        self._save()
        return location

    # READ
    def get_all(self) -> List[Location]:
        return self.locations

    def get_by_id(self, location_id: int) -> Optional[Location]:
        return next((l for l in self.locations if l.location_id == location_id), None)

    # UPDATE
    def update(
        self,
        location_id: int,
        name: Optional[str] = None,
        zone: Optional[str] = None,
        capacity: Optional[int] = None
    ) -> bool:

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
        self._save()
        return True

    # DELETE
    def remove(self, location_id: int) -> bool:
        original_len = len(self.locations)
        self.locations = [l for l in self.locations if l.location_id != location_id]

        if len(self.locations) < original_len:
            self._save()
            return True

        return False

    # SEARCH
    def search(self, keyword: str) -> List[Location]:
        keyword = keyword.lower()
        return [
            l for l in self.locations
            if keyword in l.name.lower()
            or keyword in (l.zone or "").lower()
        ]

    # SAVE
    def _save(self) -> None:
        self.repo.save([l.to_dict() for l in self.locations])



# LocationController е важен,защото иначе няма кой да управлява:
# създаване на локации
# списък с локации
# връзка между склад и локация
# евентуално търсене по локация
