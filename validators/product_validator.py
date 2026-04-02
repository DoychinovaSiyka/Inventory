class ProductValidator:

    @staticmethod
    def validate_name(name):
        if not name or not name.strip():
            raise ValueError("Името е задължително!")

    @staticmethod
    def validate_categories(category_ids):
        if not category_ids:
            raise ValueError("Трябва да изберете поне една категория.")
        for cid in category_ids:
            if not isinstance(cid, str) or len(cid.strip()) == 0:
                raise ValueError("Невалидна категория.")

    # --- НОВ МЕТОД ЗА ЛОКАЦИЯТА ---
    @staticmethod
    def validate_location(location_id):
        if not location_id or not str(location_id).strip():
            raise ValueError("Локацията на продукта е задължителна.")
        # Тук не проверяваме дали е число, защото вече ползваме "W1", "W2"
        if len(str(location_id)) > 10:
            raise ValueError("Невалиден формат на кода на локацията.")

    @staticmethod
    def validate_quantity(quantity):
        if not isinstance(quantity, (int, float)):
            raise ValueError("Количеството трябва да е число.")
        if quantity < 0: # Промених го на < 0, защото продукт може да има 0 наличност
            raise ValueError("Количеството не може да бъде отрицателно.")

    @staticmethod
    def validate_unit(unit):
        if not unit or not unit.strip():
            raise ValueError("Мерната единица е задължителна.")
        allowed_units = ["бр.", "кг", "г", "л", "мл", "стек", "кашон"]
        if unit not in allowed_units:
            raise ValueError(f"Невалидна мерна единица. Разрешени: {', '.join(allowed_units)}")

    @staticmethod
    def validate_description(description):
        if not description or not description.strip():
            raise ValueError("Описанието е задължително!")
        if len(description) > 255:
            raise ValueError("Описанието не може да бъде повече от 255 символа.")

    @staticmethod
    def validate_price(price):
        if not isinstance(price, (int, float)):
            raise ValueError("Цената трябва да е число.")
        if price <= 0:
            raise ValueError("Цената трябва да е положителна.")


    @staticmethod
    def validate_all(name, category_ids, quantity, unit, description, price, location_id=None):
        ProductValidator.validate_name(name)
        ProductValidator.validate_categories(category_ids)
        ProductValidator.validate_quantity(quantity)
        ProductValidator.validate_unit(unit)
        ProductValidator.validate_description(description)
        ProductValidator.validate_price(price)
        # Валидираме локацията само ако е подадена
        if location_id:
            ProductValidator.validate_location(location_id)

    @staticmethod
    def validate_categories(category_ids, category_controller=None):
        if not category_ids:
            raise ValueError("Трябва да изберете поне една категория.")

        for cid in category_ids:
            if not isinstance(cid, str) or len(cid.strip()) == 0:
                raise ValueError("Невалидна категория.")

            # --- НОВА ЛОГИКА (ОПЦИОНАЛНО) ---
            if category_controller:
                # Проверяваме дали тази категория съществува
                cat = category_controller.get_by_id(cid)
                if not cat:
                    raise ValueError(f"Категория с ID {cid} не съществува.")