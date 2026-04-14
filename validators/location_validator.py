class LocationValidator:

    @staticmethod
    def validate_name(name):
        if not name or not name.strip():
            raise ValueError("Името на локацията е задължително.")
        if len(name) > 100:
            raise ValueError("Името на локацията е твърде дълго.")

    # ZONE
    @staticmethod
    def validate_zone(zone):
        if zone is not None and len(zone) > 50:
            raise ValueError("Зоната/секторът не може да бъде повече от 50 символа.")


    @staticmethod
    def validate_capacity(capacity):
        # Позволяваме capacity да идва като текст от input()
        if isinstance(capacity, str):
            if not capacity.strip().isdigit():
                raise ValueError("Капацитетът трябва да е цяло число.")
            capacity = int(capacity)

        if not isinstance(capacity, int):
            raise ValueError("Капацитетът трябва да е цяло число.")

        if capacity < 0:
            raise ValueError("Капацитетът трябва да е >= 0.")

        return capacity  # връщаме нормализирана стойност

    # MASTER VALIDATION
    @staticmethod
    def validate_all(name, zone, capacity):
        LocationValidator.validate_name(name)
        LocationValidator.validate_zone(zone)
        return LocationValidator.validate_capacity(capacity)

    # UNIQUE NAME
    @staticmethod
    def validate_unique_name(name, locations, exclude_id=None):
        for l in locations:
            if l.name.lower() == name.lower() and l.location_id != exclude_id:
                raise ValueError("Локация с това име вече съществува.")

    # EXISTS
    @staticmethod
    def validate_exists(location_id, locations):
        exists = any(str(l.location_id) == str(location_id) for l in locations)
        if not exists:
            raise ValueError(f"Локация с код '{location_id}' не съществува.")
