class CategoryValidator:

    @staticmethod
    def validate_name(name):
        if not isinstance(name, str):
            raise ValueError("Името на категорията трябва да е текст.")

        cleaned = name.strip()
        if cleaned == "":
            raise ValueError("Името на категорията е задължително.")
        if len(cleaned) < 2:
            raise ValueError("Името е твърде кратко (минимум 2 символа).")
        if len(cleaned) > 50:
            raise ValueError("Името не може да надвишава 50 символа.")

        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZабвгдежзийклмнопрстуфхцчшщъьюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЮЯ0123456789 -().,\"„“–—/\\"
        for ch in cleaned:
            if ch not in allowed:
                raise ValueError(f"Името съдържа невалиден символ: '{ch}'")

    @staticmethod
    def validate_unique(name, existing_categories):
        target = name.strip().lower()
        for c in existing_categories:
            if c.name.strip().lower() == target:
                raise ValueError(f"Категория с име '{name.strip()}' вече съществува.")

    @staticmethod
    def validate_update_name(new_name):
        CategoryValidator.validate_name(new_name)

    @staticmethod
    def validate_description(description):
        if description is None:
            raise ValueError("Описанието е задължително.")
        if not isinstance(description, str):
            raise ValueError("Описанието трябва да е текст.")

        cleaned = description.strip()
        if cleaned == "":
            raise ValueError("Описанието е задължително.")
        if len(cleaned) < 3:
            raise ValueError("Описанието е твърде кратко (минимум 3 символа).")
        if len(cleaned) > 200:
            raise ValueError("Описанието е твърде дълго (максимум 200 символа).")

        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZабвгдежзийклмнопрстуфхцчшщъьюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЮЯ0123456789 -().,!?:\"„“–—"
        for ch in cleaned:
            if ch not in allowed:
                raise ValueError(f"Описанието съдържа невалиден символ: '{ch}'")

        return cleaned

    @staticmethod
    def validate_parent_id(parent_id, category_id):
        if parent_id and category_id and str(parent_id) == str(category_id):
            raise ValueError("Категория не може да бъде родител на самата себе си.")

    @staticmethod
    def validate_parent_exists(parent_id, categories):
        if not parent_id:
            return
        for c in categories:
            if str(c.category_id) == str(parent_id):
                return
        raise ValueError("Родителската категория не е намерена (проверете ID-то).")

    @staticmethod
    def validate_parent_choice(choice):
        if not choice:
            return None
        cleaned = choice.strip()
        for ch in cleaned:
            if not (ch.isalnum() or ch == "-"):
                raise ValueError("Невалиден формат за ID на родителска категория.")
        return cleaned

    @staticmethod
    def validate_no_cycle(category_id, parent_id, categories):
        if not parent_id:
            return

        target = str(category_id)
        current = parent_id

        while current:
            if str(current) == target:
                raise ValueError("Открита циклична зависимост между категориите.")

            next_parent = None
            for c in categories:
                if str(c.category_id) == str(current):
                    next_parent = c.parent_id
                    break

            current = next_parent

    @staticmethod
    def validate_can_delete(category_id, all_categories, products):
        target_id = str(category_id)

        # Проверка за подкатегории
        for c in all_categories:
            if str(c.parent_id) == target_id:
                raise ValueError("Категорията има подкатегории. Първо преместете или изтрийте тях.")

        # Проверка за продукти
        for p in products:
            if p.categories:
                for cat in p.categories:
                    if str(cat.category_id) == target_id:
                        raise ValueError(f"Категорията се използва от продукт '{p.name}'.")

    @staticmethod
    def validate_exists(category_id, categories):
        for c in categories:
            if str(c.category_id) == str(category_id):
                return c
        raise ValueError("Категорията не е намерена.")
