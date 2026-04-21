class LocationValidator:

    @staticmethod
    def validate_name(name):
        if not isinstance(name, str):
            raise ValueError("Името на локацията трябва да е текст.")

        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Името на локацията е задължително.")

        if len(cleaned) < 2:
            raise ValueError("Името е твърде кратко.")

        if len(cleaned) > 100:
            raise ValueError("Името на локацията е твърде дълго.")

        allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЬЮЯабвгдежзийклмнопрстуфхцчшщъьюя0123456789 -–—.,()\"„“"
        for ch in cleaned:
            if ch not in allowed:
                raise ValueError("Името съдържа невалидни символи.")

        return cleaned

    @staticmethod
    def validate_zone(zone):
        if zone is None:
            return ""

        if not isinstance(zone, str):
            raise ValueError("Зоната/секторът трябва да е текст.")

        cleaned = zone.strip()
        if len(cleaned) > 50:
            raise ValueError("Зоната/секторът не може да бъде повече от 50 символа.")

        return cleaned

    @staticmethod
    def validate_capacity(capacity):
        if isinstance(capacity, str):
            if not capacity.strip().isdigit():
                raise ValueError("Капацитетът трябва да е цяло число.")
            capacity = int(capacity)

        if not isinstance(capacity, int):
            raise ValueError("Капацитетът трябва да е цяло число.")

        if capacity <= 0:
            raise ValueError("Капацитетът трябва да е положително число.")

        return capacity

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
