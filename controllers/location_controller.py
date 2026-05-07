from typing import Optional, List
from models.location import Location
from validators.location_validator import LocationValidator


class LocationController:
    """Контролерът управлява локациите в системата."""

    def __init__(self, repo, activity_log_controller=None, inventory_controller=None):
        self.repo = repo
        self.activity_log = activity_log_controller
        self.inventory_controller = inventory_controller

        # Зареждане на локациите
        raw = self.repo.load()
        if not raw or not isinstance(raw, list):
            raw = []
        self.locations: List[Location] = [Location.from_dict(l) for l in raw]

    def _log(self, action: str, message: str):
        if self.activity_log:
            self.activity_log.log_action("system", action, message)


    # CREATE
    def add(self, name: str, zone: str = "", capacity=None) -> Location:
        name = LocationValidator.validate_name(name)
        zone = LocationValidator.validate_zone(zone)
        capacity = LocationValidator.validate_capacity(capacity)

        LocationValidator.validate_unique_name(name, self.locations)
        location = Location(location_id=None, name=name, zone=zone, capacity=capacity)
        self.locations.append(location)
        self.save_changes()

        short_id = location.location_id[:8]
        self._log("ADD_LOCATION", f"Добавена локация: {name} (ID: {short_id})")

        return location

    # READ
    def get_all(self) -> List[Location]:
        return self.locations

    def get_by_id(self, location_id: str) -> Optional[Location]:
        target_id = str(location_id).strip()
        if not target_id:
            return None

        for loc in self.locations:
            if loc.location_id.startswith(target_id):
                return loc
        return None

    def update(self, location_id: str, name: Optional[str] = None, zone: Optional[str] = None, capacity=None) -> bool:
        location = self.get_by_id(location_id)
        if location is None:
            raise ValueError(f"Локация с ID {location_id} не съществува.")

        if name is not None:
            name = LocationValidator.validate_name(name)
            LocationValidator.validate_unique_name(name, self.locations, exclude_id=location.location_id)
            location.name = name

        if zone is not None:
            zone = LocationValidator.validate_zone(zone)
            location.zone = zone

        if capacity is not None:
            capacity = LocationValidator.validate_capacity(capacity)
            location.capacity = capacity

        location.update_modified()
        self.save_changes()
        self._log("EDIT_LOCATION", f"Обновена локация {location.location_id[:8]}")

        return True

    def remove(self, location_id: str) -> bool:
        location = self.get_by_id(location_id)
        if location is None:
            raise ValueError(f"Локация с ID {location_id} не съществува.")

        # Проверка за наличности
        if self.inventory_controller:
            stock = self.inventory_controller.get_stock_by_location(location.location_id)
            if stock and sum(item.quantity for item in stock) > 0:
                raise ValueError("Локацията съдържа стока и не може да бъде изтрита.")

        full_id = location.location_id
        self.locations = [l for l in self.locations if l.location_id != full_id]
        self.save_changes()
        self._log("DELETE_LOCATION", f"Изтрита локация {full_id[:8]}")
        return True

    def save_changes(self) -> None:
        # Записваме пълните 36-символни UUID в JSON файла
        self.repo.save([l.to_dict() for l in self.locations])