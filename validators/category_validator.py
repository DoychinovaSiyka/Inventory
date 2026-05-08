class CategoryValidator:

    @staticmethod
    def validate_name(name):
        if not isinstance(name, str):
            raise ValueError("Името трябва да е текст.")

        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Името е задължително.")

        if not (2 <= len(cleaned) <= 50):
            raise ValueError("Името трябва да е между 2 и 50 символа.")

        return cleaned

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
        return choice.strip()

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

        for c in all_categories:
            if str(c.parent_id) == target_id:
                raise ValueError("Категорията има подкатегории. Първо преместете или изтрийте тях.")

        for p in products:
            if target_id in p.get_category_ids():
                raise ValueError(f"Категорията се използва от продукт '{p.name}'.")

    @staticmethod
    def validate_exists(category_id, categories):
        for c in categories:
            if str(c.category_id) == str(category_id):
                return c
        raise ValueError("Категорията не е намерена.")
