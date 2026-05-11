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
        if isinstance(capacity, str):
            cleaned = capacity.strip()

            if cleaned.startswith("0") and cleaned != "0":
                raise ValueError("Капацитетът не може да започва с 0.")

            if not cleaned.isdigit():
                raise ValueError("Капацитетът трябва да съдържа само цифри.")

            capacity = int(cleaned)

        if not isinstance(capacity, int):
            raise ValueError("Капацитетът трябва да е цяло число.")
        if capacity <= 0:
            raise ValueError("Капацитетът трябва да е положително число.")

        return capacity
