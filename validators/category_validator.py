import re

class CategoryValidator:


    @staticmethod
    def validate_name(name):
        if not isinstance(name, str):
            raise ValueError("Името на категорията трябва да е текст.")

        cleaned = name.strip()
        if not cleaned:
            raise ValueError("Името на категорията е задължително.")
        if len(cleaned) < 2:
            raise ValueError("Името е твърде кратко (минимум 2 символа).")
        if len(cleaned) > 50:
            raise ValueError("Името не може да надвишава 50 символа.")

        # Разрешавам букви, цифри, интервали, тирета (всички видове), кавички, запетайки, точки и скоби
        if not re.match(r'^[A-Za-zА-Яа-я0-9 \-–—.,()"„“]+$', cleaned):
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
        if description is None or description.strip() == "":
            raise ValueError("Описанието е задължително.")

        if not isinstance(description, str):
            raise ValueError("Описанието трябва да е текст.")

        cleaned = description.strip()
        if len(cleaned) < 3:
            raise ValueError("Описанието е твърде кратко (минимум 3 символа).")
        if len(cleaned) > 200:
            raise ValueError("Описанието е твърде дълго (максимум 200 символа).")
        if not re.match(r'^[A-Za-zА-Яа-я0-9 \-–—.,!?()\"„“]+$', cleaned):
            raise ValueError("Описанието съдържа невалидни символи.")

        return cleaned

    @staticmethod
    def validate_parent_id(parent_id, category_id):
        if parent_id and category_id and str(parent_id) == str(category_id):
            raise ValueError("Категория не може да бъде подкатегория на самата себе си.")

    @staticmethod
    def validate_parent_exists(parent_id, categories):
        if parent_id is None or parent_id == "":
            return
        exists = any(str(c.category_id) == str(parent_id) for c in categories)
        if not exists:
            raise ValueError("Родителската категория не съществува.")

    @staticmethod
    def validate_parent_choice(choice):
        if choice is None or choice.strip() == "":
            return None

        cleaned = choice.strip()
        if cleaned.isdigit():
            return int(cleaned)
        if re.match(r"^[A-Za-z0-9\-\_]+$", cleaned):
            return cleaned

        raise ValueError("Невалиден формат за родителска категория.")

    @staticmethod
    def validate_no_cycle(category_id, parent_id, all_categories):
        if parent_id is None:
            return
        current = parent_id
        while current:
            parent = next((c for c in all_categories if c.category_id == current), None)
            if not parent:
                break
            if parent.category_id == category_id:
                raise ValueError("Открита циклична зависимост между категориите.")
            current = parent.parent_id

    @staticmethod
    def validate_can_delete(category_id, all_categories, products):
        for c in all_categories:
            if c.parent_id == category_id:
                raise ValueError("Категорията има подкатегории и не може да бъде изтрита.")

        for p in products:
            if p.category_id == category_id:
                raise ValueError("Категорията съдържа продукти и не може да бъде изтрита.")

    @staticmethod
    def validate_exists(category_id, controller):
        category = controller.get_by_id(category_id)
        if not category:
            raise ValueError("Категорията не е намерена.")
        return category
