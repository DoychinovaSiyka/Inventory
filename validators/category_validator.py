
class CategoryValidator:

    @staticmethod
    def validate_name(name):
        if not isinstance(name,str):
            raise ValueError("Името на категорията трябва да е текст.")
        if not name or not name.strip():
            raise ValueError("Името на категорията е задължително.")
        if len(name.strip()) > 50:
            raise ValueError("Името на категорията не може да надвишава 50 символа.")
    @staticmethod
    def validate_unique(name, existing_categories):
        for c in existing_categories:
            if c.name.lower() == name.lower():
                raise ValueError("Категория с това име вече съществува.")

    @staticmethod
    def validate_update_name(new_name):
        CategoryValidator.validate_name(new_name)

    @staticmethod
    def validate_description(description):
        if description is None:
            return
        if not isinstance(description,str):
            raise ValueError("Описанието трябва да е текст.")
        if len(description) > 200:
            raise ValueError("Описанието е твърде дълго (максимум 200 символа).")
