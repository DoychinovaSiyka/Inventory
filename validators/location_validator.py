class LocationValidator:

    @staticmethod
    def validate_name(name):
        if not isinstance(name, str):
            raise ValueError("Името на локацията трябва да е текст.")

        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Името на локацията е задължително.")

        if len(cleaned) > 100:
            raise ValueError("Името на локацията е твърде дълго.")

        return cleaned  # ← ВАЖНО: връщаме нормализирано име

    @staticmethod
    def validate_zone(zone):
        if zone is None:
            return ""  # позволяваме празна зона, но не None

        if not isinstance(zone, str):
            raise ValueError("Зоната/секторът трябва да е текст.")

        cleaned = zone.strip()

        if len(cleaned) > 50:
            raise ValueError("Зоната/секторът не може да бъде повече от 50 символа.")

        return cleaned  # ← ВАЖНО: връщаме нормализирана зона

    @staticmethod
    def validate_capacity(capacity):
        if isinstance(capacity, str):
            if not capacity.strip().isdigit():
                raise ValueError("Капацитетът трябва да е цяло число.")
            capacity = int(capacity)

        if not isinstance(capacity, int):
            raise ValueError("Капацитетът трябва да е цяло число.")

        if capacity < 0:
            raise ValueError("Капацитетът трябва да е >= 0.")

        return capacity

    @staticmethod
    def validate_all(name, zone, capacity):
        name = LocationValidator.validate_name(name)
        zone = LocationValidator.validate_zone(zone)
        capacity = LocationValidator.validate_capacity(capacity)
        return name, zone, capacity

    @staticmethod
    def validate_unique_name(name, locations, exclude_id=None):
        target = name.strip().lower()
        for l in locations:
            if l.name.strip().lower() == target and l.location_id != exclude_id:
                raise ValueError("Локация с това име вече съществува.")

    @staticmethod
    def validate_exists(location_id, locations):
        exists = any(str(l.location_id) == str(location_id) for l in locations)
        if not exists:
            raise ValueError(f"Локация с код '{location_id}' не съществува.")
