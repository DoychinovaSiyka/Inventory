from typing import Optional, List
from models.location import Location
from validators.location_validator import LocationValidator


class LocationController:
    """Контролерът управлява локациите в системата."""
    def __init__(self, repo, activity_log_controller=None, inventory_controller=None):
        self.repo = repo
        self.inventory_controller = inventory_controller

        raw = self.repo.load()
        if not raw or not isinstance(raw, list):
            raw = []

        self.locations: List[Location] = []
        for l in raw:
            obj = Location.from_dict(l)
            if obj:
                self.locations.append(obj)



    def save(self) -> None:
        self._save_changes()


    def add(self, name: str, zone: str = "", capacity=None) -> Location:
        name = LocationValidator.validate_name(name)
        zone = LocationValidator.validate_zone(zone)
        capacity = LocationValidator.validate_capacity(capacity)

        LocationValidator.validate_unique_name(name, self.locations)

        location = Location(location_id=None, name=name, zone=zone, capacity=capacity)
        self.locations.append(location)
        self._save_changes()

        return location



    def get_all(self) -> List[Location]:
        return self.locations

    def get_by_id(self, location_id: str) -> Optional[Location]:
        target = str(location_id or "").strip().lower()

        for loc in self.locations:
            if loc.location_id[:8].lower() == target:
                return loc

        return None


    def search(self, query: str) -> List[Location]:
        q = str(query or "").strip().lower()
        if not q:
            return []

        results = []
        for loc in self.locations:
            short_id = loc.location_id[:8].lower()
            name = loc.name.lower()
            zone = loc.zone.lower()
            cap = str(loc.capacity).lower()


            if (q in short_id or q in name or q in zone or q in cap):
                results.append(loc)

        return results


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
        self._save_changes()
        return True


    def remove(self, location_id: str) -> bool:
        location = self.get_by_id(location_id)
        if location is None:
            raise ValueError(f"Локация с ID {location_id} не съществува.")

        # Проверка за наличности
        if self.inventory_controller:
            products_data = self.inventory_controller.data.get("products", {})

            for pid, pdata in products_data.items():
                locations_map = pdata.get("locations", {})

                normalized_map = {}
                for key, qty in locations_map.items():
                    loc_obj = self.get_by_id(key)
                    if loc_obj:
                        normalized_map[loc_obj.location_id] = qty
                    else:
                        normalized_map[key] = qty

                qty = normalized_map.get(location.location_id, 0)

                try:
                    qty_value = float(qty)
                except Exception:
                    qty_value = 0.0

                if qty_value > 0:
                    raise ValueError("Локацията съдържа стока и не може да бъде изтрита.")

        full_id = location.location_id
        self.locations = [l for l in self.locations if l.location_id != full_id]
        self._save_changes()
        return True



    def _save_changes(self) -> None:
        data = [l.to_dict() for l in self.locations]
        self.repo.save(data)
