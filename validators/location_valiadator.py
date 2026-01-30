class LocationValidator:

    @staticmethod
    def validate_name(name):
        if not name or not name.strip():
            raise ValueError("Името на локацията е задължително.")

        if len(name) > 100:
            raise ValueError("Името на локацията е твърде дълго.")

    @staticmethod
    def validate_zone(zone):
        if zone is not None and len(zone) > 50:
            raise ValueError("Зоната/секторът не може да бъде повече от 50 символа.")
    @staticmethod
    def validate_capacity(capacity):
        if not isinstance(capacity,int):
            raise ValueError("Капацитетът трябва да е цяло число.")
        if  capacity < 0:
            raise ValueError("Капацитетът трябва да е >= 0.")
    @staticmethod
    def validate_all(name,zone,capacity):
        LocationValidator.validate_name(name)
        LocationValidator.validate_zone(zone)
        LocationValidator.validate_capacity(capacity)


