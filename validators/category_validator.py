# validators/category_validator.py

class CategoryValidator:

    @staticmethod
    def validate_name(name):
        if not name or not name.strip():
            raise ValueError("Името на категорията е задължително.")

        if len(name) > 50:
            raise ValueError("Името на категорията не може да надвишава 50 символа.")

    @staticmethod
    def validate_unique(name, existing_categories):
        for c in existing_categories:
            if c.name.lower() == name.lower():
                raise ValueError("Категория с това име вече съществува.")

    @staticmethod
    def validate_update_name(new_name):
        if not new_name or not new_name.strip():
            raise ValueError("Новото име е задължително.")
