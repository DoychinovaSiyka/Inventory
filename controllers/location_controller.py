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

        self.locations: List[Location] = []
        for l in raw:
            obj = Location.from_dict(l)
            if obj:
                self.locations.append(obj)

    def _log(self, action: str, message: str):
        if self.activity_log:
            self.activity_log.log_action("system", action, message)

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

    def update(self, location_id: str, name: Optional[str] = None,
               zone: Optional[str] = None, capacity=None) -> bool:

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

        # Проверка за наличности (поправена логика)
        if self.inventory_controller:
            products_data = self.inventory_controller.data.get("products", {})

            for pid, pdata in products_data.items():
                locations_map = pdata.get("locations", {})
                qty = locations_map.get(location.location_id, 0)

                try:
                    qty_value = float(qty)
                except Exception:
                    qty_value = 0.0

                if qty_value > 0:
                    raise ValueError("Локацията съдържа стока и не може да бъде изтрита.")

        full_id = location.location_id

        new_list = []
        for l in self.locations:
            if l.location_id != full_id:
                new_list.append(l)

        self.locations = new_list
        self.save_changes()

        self._log("DELETE_LOCATION", f"Изтрита локация {full_id[:8]}")
        return True

    def save_changes(self) -> None:
        data = []
        for l in self.locations:
            data.append(l.to_dict())
        self.repo.save(data)
