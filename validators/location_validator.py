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
            raise ValueError("Името на локацията е твърде дълго.")

        allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЬЮЯабвгдежзийклмнопрстуфхцчшщъьюя0123456789 -–—.,()\"„“/\\"
        for ch in cleaned:
            if ch not in allowed:
                raise ValueError(f"Името съдържа невалиден символ: '{ch}'")
        return cleaned

    @staticmethod
    def validate_zone(zone):
        if zone is None or zone == "":
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
            cleaned = capacity.strip()
            if not cleaned.isdigit():
                raise ValueError("Капацитетът трябва да съдържа само цифри.")
            capacity = int(cleaned)

        if not isinstance(capacity, int):
            raise ValueError("Капацитетът трябва да е цяло число.")
        if capacity <= 0:
            raise ValueError("Капацитетът трябва да е положително число (напр. брой палетни места).")
        return capacity

    @staticmethod
    def validate_unique_name(name, locations, exclude_id=None):
        target = name.strip().lower()
        for l in locations:
            if l.name.strip().lower() == target:
                if exclude_id and str(l.location_id) == str(exclude_id):
                    continue
                raise ValueError(f"Локация с име '{name.strip()}' вече съществува.")

    @staticmethod
    def validate_exists(location_id, locations):
        search_id = str(location_id).strip().lower()
        exists = any(str(l.location_id).lower().startswith(search_id) for l in locations)

        if not exists:
            raise ValueError(f"Склад/Локация с код '{location_id}' не е намерен в базата.")

    @staticmethod
    def validate_can_delete(location_id, inventory_controller):
        stock_in_loc = inventory_controller.get_stock_by_location_total(location_id)
        if stock_in_loc > 0:
            raise ValueError(
                f"Локацията не може да бъде изтрита, защото в нея има {stock_in_loc} налични единици стока."
            )
