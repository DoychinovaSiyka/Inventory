class LocationValidator:

    @staticmethod
    def validate_name(name):
        if not isinstance(name, str):
            raise ValueError("Името на локацията трябва да е текст.")

        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Името на локацията е задължително.")
        if len(cleaned) < 2:
            raise ValueError("Името е твърде кратко (минимум 2 символа).")
        if len(cleaned) > 100:
            raise ValueError("Името е твърде дълго.")
        return cleaned

    @staticmethod
    def validate_unique_name(name, locations, exclude_id=None):
        """Проверява дали името вече съществува в списъка с локации."""
        cleaned_name = name.strip().lower()
        for loc in locations:
            if loc.name.lower() == cleaned_name and loc.location_id != exclude_id:
                raise ValueError(f"Локация с име '{name}' вече съществува.")
        return name

    @staticmethod
    def validate_code(code, locations, exclude_id=None):
        """Валидира и проверява за уникалност краткия код (напр. W1, A10)."""
        if code is None:
            return ""

        cleaned = str(code).strip().upper()

        if not cleaned:
            raise ValueError("Кодът на локацията е задължителен.")

        if len(cleaned) > 10:
            raise ValueError("Кодът не може да бъде по-дълъг от 10 символа.")

        # Проверка за уникалност в списъка
        for loc in locations:
            # Проверяваме дали кодът съществува и дали не принадлежи на същата локация (при update)
            if hasattr(loc, 'code') and loc.code:
                if loc.code.upper() == cleaned and loc.location_id != exclude_id:
                    raise ValueError(f"Кодът '{cleaned}' вече е зает от друга локация.")

        return cleaned

    @staticmethod
    def validate_zone(zone):
        if zone is None or zone.strip() == "":
            raise ValueError("Зоната/секторът е задължителна.")

        if not isinstance(zone, str):
            raise ValueError("Зоната/секторът трябва да е текст.")

        cleaned = zone.strip()
        if len(cleaned) < 2:
            raise ValueError("Зоната трябва да е поне 2 символа.")
        if len(cleaned) > 50:
            raise ValueError("Зоната/секторът не може да бъде повече от 50 символа.")

        return cleaned

    @staticmethod
    def validate_capacity(capacity):
        if capacity is None:
            raise ValueError("Капацитетът е задължителен.")

        if isinstance(capacity, str):
            cleaned = capacity.strip()
            if not cleaned:
                raise ValueError("Капацитетът не може да е празен.")

            if cleaned.startswith("0") and cleaned != "0":
                raise ValueError("Капацитетът не може да започва с 0.")

            if not cleaned.isdigit():
                raise ValueError("Капацитетът трябва да съдържа само цели числа.")

            capacity = int(cleaned)

        if not isinstance(capacity, int):
            raise ValueError("Капацитетът трябва да е цяло число.")

        if capacity <= 0:
            raise ValueError("Капацитетът трябва да е положително число.")

        return capacity