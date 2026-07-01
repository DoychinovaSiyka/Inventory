from typing import Optional, List
from models.location import Location
from validators.location_validator import LocationValidator
from controllers.abstract_controller import AbstractController


class LocationController(AbstractController):
    """Чист MVC контролер за локации – без цикличност, без enterprise зависимости."""

    def __init__(self, repo):
        super().__init__(repo)
        self.locations = self.load() or []

    def from_dict(self, data):
        return Location.from_dict(data)

    def to_dict(self, obj):
        return obj.to_dict()

    def _save(self):
        self.save(self.locations)

    # -----------------------------
    # ADD
    # -----------------------------
    def add(self, name: str, zone: str = "", capacity=None, code: str = "") -> Location:
        name = LocationValidator.validate_name(name)
        zone = LocationValidator.validate_zone(zone)
        capacity = LocationValidator.validate_capacity(capacity)
        LocationValidator.validate_unique_name(name, self.locations)

        code = LocationValidator.validate_code(code, self.locations)

        location = Location(
            location_id=None,
            name=name,
            zone=zone,
            capacity=capacity,
            code=code
        )

        self.locations.append(location)
        self._save()
        return location

    # -----------------------------
    # GETTERS
    # -----------------------------
    def get_all(self) -> List[Location]:
        return self.locations

    def get_by_id(self, identifier: str) -> Optional[Location]:
        if not identifier:
            return None

        target = str(identifier).strip().lower()

        for loc in self.locations:
            if loc.location_id.lower() == target:
                return loc
            if loc.location_id[:8].lower() == target:
                return loc
            if loc.code and loc.code.lower() == target:
                return loc

        return None

    # -----------------------------
    # SEARCH
    # -----------------------------
    def search(self, query: str) -> List[dict]:
        q = str(query or "").strip().lower()
        if not q:
            return []

        results = []
        for loc in self.locations:
            short_id = loc.location_id[:8].lower()
            name = loc.name.lower()
            zone = loc.zone.lower()
            cap = str(loc.capacity).lower()
            code = str(loc.code or "").lower()

            if q in short_id or q in name or q in zone or q in cap or q in code:
                results.append({
                    "id": loc.location_id[:8],
                    "name": loc.name,
                    "zone": loc.zone,
                    "capacity": loc.capacity,
                    "code": loc.code
                })

        return results

    # -----------------------------
    # UPDATE
    # -----------------------------
    def update(self, location_id: str, name: Optional[str] = None,
               zone: Optional[str] = None, capacity=None, code: Optional[str] = None) -> bool:

        location = self.get_by_id(location_id)
        if location is None:
            raise ValueError(f"Локация с идентификатор {location_id} не съществува.")

        if name is not None:
            name = LocationValidator.validate_name(name)
            LocationValidator.validate_unique_name(name, self.locations, exclude_id=location.location_id)
            location.name = name

        if zone is not None:
            location.zone = LocationValidator.validate_zone(zone)

        if capacity is not None:
            location.capacity = LocationValidator.validate_capacity(capacity)

        if code is not None:
            location.code = LocationValidator.validate_code(code, self.locations, exclude_id=location.location_id)

        location.update_modified()
        self._save()
        return True

    # -----------------------------
    # REMOVE (чист MVC – без inventory_controller)
    # -----------------------------
    def remove(self, location_id: str) -> bool:
        location = self.get_by_id(location_id)
        if location is None:
            raise ValueError(f"Локация с идентификатор {location_id} не съществува.")

        # Чист MVC: контролерът НЕ проверява инвентара.
        # Проверка за наличности се прави в InventoryController или MovementController.

        self.locations = [l for l in self.locations if l.location_id != location.location_id]
        self._save()
        return True

    def get_all_dict(self):
        return {str(loc.location_id): loc for loc in self.get_all()}

    # -----------------------------
    # VALIDATION
    # -----------------------------
    def validate_field(self, field_type: str, value: str) -> Optional[str]:
        try:
            if field_type == "name":
                LocationValidator.validate_name(value)
            elif field_type == "zone":
                LocationValidator.validate_zone(value)
            elif field_type == "capacity":
                LocationValidator.validate_capacity(value)
            elif field_type == "code":
                if not value.strip():
                    raise ValueError("Кодът не може да е празен.")
            return None
        except ValueError as e:
            return str(e)
