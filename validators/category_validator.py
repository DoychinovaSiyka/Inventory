class CategoryValidator:

    @staticmethod
    def validate_name(name):
        if not isinstance(name, str):
            raise ValueError("Името на категорията трябва да е текст.")

        cleaned_name = name.strip()
        if not cleaned_name:
            raise ValueError("Името на категорията е задължително.")

        if len(cleaned_name) < 2:
            raise ValueError("Името е твърде кратко (минимум 2 символа).")

        if len(cleaned_name) > 50:
            raise ValueError("Името на категорията не може да надвишава 50 символа.")

    @staticmethod
    def validate_unique(name, existing_categories):
        target_name = name.strip().lower()
        for c in existing_categories:
            if c.name.strip().lower() == target_name:
                raise ValueError(f"Категория с име '{name.strip()}' вече съществува.")

    @staticmethod
    def validate_update_name(new_name):
        CategoryValidator.validate_name(new_name)


    # DESCRIPTION VALIDATION
    @staticmethod
    def validate_description(description):
        if description is None or description == "":
            return
        if not isinstance(description, str):
            raise ValueError("Описанието трябва да е текст.")
        if len(description) > 200:
            raise ValueError("Описанието е твърде дълго (максимум 200 символа).")

    # PARENT VALIDATION
    @staticmethod
    def validate_parent_id(parent_id, category_id):
        """Проверява дали категорията не се опитва да бъде родител на самата себе си."""
        if parent_id and category_id and str(parent_id) == str(category_id):
            raise ValueError("Една категория не може да бъде подкатегория на самата себе си!")
