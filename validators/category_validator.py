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

        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZабвгдежзийклмнопрстуфхцчшщъьюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЮЯ0123456789 -().,\"„“"
        for ch in cleaned:
            if ch not in allowed:
                raise ValueError("Името съдържа невалидни символи.")

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

        # Проверка за позволени символи
        allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZабвгдежзийклмнопрстуфхцчшщъьюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЮЯ0123456789 -().,!?:\"„“"
        for ch in cleaned:
            if ch not in allowed:
                raise ValueError("Описанието съдържа невалидни символи.")

        return cleaned

    @staticmethod
    def validate_parent_id(parent_id, category_id):
        if parent_id is not None and parent_id != "":
            if str(parent_id) == str(category_id):
                raise ValueError("Категория не може да бъде подкатегория на самата себе си.")

    @staticmethod
    def validate_parent_exists(parent_id, categories):
        if parent_id is None or parent_id == "":
            return
        found = False
        for c in categories:
            if str(c.category_id) == str(parent_id):
                found = True
                break
        if not found:
            raise ValueError("Родителската категория не съществува.")

    @staticmethod
    def validate_parent_choice(choice):
        if choice is None:
            return None

        cleaned = choice.strip()
        if cleaned == "":
            return None
        for ch in cleaned:
            if not (ch.isalnum() or ch in "-_"):
                raise ValueError("Невалиден формат за родителска категория.")
        return cleaned

    @staticmethod
    def validate_no_cycle(category_id, parent_id, all_categories):
        if parent_id is None or parent_id == "":
            return

        current = parent_id
        while current:
            parent = None
            # Търсим родителя
            for c in all_categories:
                if str(c.category_id) == str(current):
                    parent = c
                    break
            if parent is None:
                break
            if str(parent.category_id) == str(category_id):
                raise ValueError("Открита циклична зависимост между категориите.")

            current = parent.parent_id

    @staticmethod
    def validate_can_delete(category_id, all_categories, products):
        target_id = str(category_id)
        # Проверка за подкатегории
        for c in all_categories:
            if str(c.parent_id) == target_id:
                raise ValueError("Категорията има подкатегории и не може да бъде изтрита.")

        for p in products:
            product_cat_ids = []
            for cat in p.categories:
                if hasattr(cat, "category_id"):
                    product_cat_ids.append(str(cat.category_id))
                else:
                    product_cat_ids.append(str(cat))
            if target_id in product_cat_ids:
                raise ValueError(f"Категорията не може да бъде изтрита, защото продуктът '{p.name}' я използва.")

    @staticmethod
    def validate_exists(category_id, controller):
        category = controller.get_by_id(category_id)
        if category is None:
            raise ValueError("Категорията не е намерена.")
        return category