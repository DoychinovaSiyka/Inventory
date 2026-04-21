from typing import Optional, List
from datetime import datetime
from models.location import Location
from storage.json_repository import JSONRepository
from validators.location_validator import LocationValidator


class LocationController:
    """Контролерът управлява локациите в системата. Работи коректно дори когато locations.json е празен."""
    def __init__(self, repo: JSONRepository, activity_log_controller=None, inventory_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller
        self.inventory_controller = inventory_controller

        raw = self.repo.load()
        if not raw or not isinstance(raw, list):
            raw = []

        self.locations: List[Location] = [Location.from_dict(l) for l in raw]

    def _log(self, action: str, message: str):
        if self.activity_log:
            self.activity_log.add_log("system", action, message)

    def _generate_id(self) -> str:
        """Генерира W1, W2, W3..."""
        if not self.locations:
            return "W1"

        numeric_ids = []
        for loc in self.locations:
            num = str(loc.location_id).replace("W", "")
            if num.isdigit():
                numeric_ids.append(int(num))

        next_id = max(numeric_ids) + 1 if numeric_ids else 1
        return f"W{next_id}"

    # CREATE
    def add(self, name: str, zone: str = "", capacity=None) -> Location:
        name = LocationValidator.validate_name(name)
        zone = LocationValidator.validate_zone(zone)
        capacity = LocationValidator.validate_capacity(capacity)

        LocationValidator.validate_unique_name(name, self.locations)

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        location = Location(location_id=self._generate_id(), name=name, zone=zone, capacity=capacity,
                            created=now, modified=now)

        self.locations.append(location)
        self.save_changes()
        self._log("ADD_LOCATION", f"Добавена локация: {name}")

        return location

    # READ
    def get_all(self) -> List[Location]:
        return self.locations

    def get_by_id(self, location_id: str) -> Optional[Location]:
        """Връща None, ако локацията не съществува (без гръмване)."""
        for loc in self.locations:
            if loc.location_id == location_id:
                return loc
        return None

    # UPDATE
    def update(self, location_id: str, name: Optional[str] = None,
               zone: Optional[str] = None, capacity=None) -> bool:

        location = self.get_by_id(location_id)
        if location is None:
            raise ValueError(f"Локация с ID {location_id} не съществува.")

        if name is not None:
            name = LocationValidator.validate_name(name)
            LocationValidator.validate_unique_name(name, self.locations, exclude_id=location_id)
            location.name = name

        if zone is not None:
            zone = LocationValidator.validate_zone(zone)
            location.zone = zone

        if capacity is not None:
            capacity = LocationValidator.validate_capacity(capacity)
            location.capacity = capacity

        location.update_modified()
        self.save_changes()
        self._log("EDIT_LOCATION", f"Обновена локация {location_id}")

        return True

    # DELETE
    def remove(self, location_id: str) -> bool:
        location = self.get_by_id(location_id)
        if location is None:
            raise ValueError(f"Локация с ID {location_id} не съществува.")

        # Дали в склада има наличности
        if self.inventory_controller:
            stock = self.inventory_controller.get_stock_by_location(location_id)
            if stock and sum(item.quantity for item in stock) > 0:
                raise ValueError("Локацията съдържа стока и не може да бъде изтрита.")

        self.locations = [l for l in self.locations if l.location_id != location_id]
        self.save_changes()
        self._log("DELETE_LOCATION", f"Изтрита локация {location_id}")

        return True

    def save_changes(self) -> None:
        self.repo.save([l.to_dict() for l in self.locations])
