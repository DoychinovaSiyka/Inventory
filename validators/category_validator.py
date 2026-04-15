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

    @staticmethod
    def validate_unique(name, existing_categories):
        """Проверява дали името вече съществува в списъка от категории."""
        target = name.strip().lower()
        for c in existing_categories:
            if c.name.strip().lower() == target:
                raise ValueError(f"Категория с име '{name.strip()}' вече съществува.")

    @staticmethod
    def validate_update_name(new_name):
        CategoryValidator.validate_name(new_name)

    # DESCRIPTION VALIDATION
    @staticmethod
    def validate_description(description):
        if description is None or description == "":
            return  # описанието е по избор

        if not isinstance(description, str):
            raise ValueError("Описанието трябва да е текст.")

        if len(description) > 200:
            raise ValueError("Описанието е твърде дълго (максимум 200 символа).")

    # PARENT VALIDATION
    @staticmethod
    def validate_parent_id(parent_id, category_id):
        """Проверява дали категорията не е родител сама на себе си."""
        if parent_id and category_id and str(parent_id) == str(category_id):
            raise ValueError("Категория не може да бъде подкатегория на самата себе си.")

    @staticmethod
    def validate_parent_choice(choice):
        """Проверява дали изборът за родител е валидно число или празно."""
        if choice is None or choice.strip() == "":
            return None
        if not choice.isdigit():
            raise ValueError("Изборът за родител трябва да е число.")
        return int(choice)

    @staticmethod
    def validate_category_choice(choice):
        """Проверява дали изборът на категория е валидно число."""
        if not choice.isdigit():
            raise ValueError("Изборът трябва да е число.")
        return int(choice)

    # CYCLE VALIDATION
    @staticmethod
    def validate_no_cycle(category_id, parent_id, all_categories):
        """Проверява за циклична зависимост (дете → родител → дете)."""
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

    # DELETE VALIDATION (оригиналната ти логика)
    @staticmethod
    def validate_can_delete(category_id, all_categories, products):
        """Проверява дали категорията може да бъде изтрита."""
        # Има подкатегории?
        for c in all_categories:
            if c.parent_id == category_id:
                raise ValueError("Категорията има подкатегории и не може да бъде изтрита.")

        # Има продукти?
        for p in products:
            if p.category_id == category_id:
                raise ValueError("Категорията съдържа продукти и не може да бъде изтрита.")

    # Проверка дали родител съществува
    @staticmethod
    def validate_parent_exists(parent_id, categories):
        if parent_id is None:
            return
        exists = any(str(c.category_id) == str(parent_id) for c in categories)
        if not exists:
            raise ValueError("Родителската категория не съществува.")

    # Проверка за изтриване с продукти и подкатегории
    @staticmethod
    def validate_can_delete_controller(category_id, categories, product_controller):
        # Забрана за изтриване, ако има подкатегории
        has_children = any(str(c.parent_id) == str(category_id) for c in categories)
        if has_children:
            raise ValueError("Не може да изтриете категория с подкатегории!")

        # Забрана за изтриване, ако има продукти
        if product_controller:
            has_products = any(
                str(category_id) in [
                    str(cat.category_id) if isinstance(cat, Category) else str(cat)
                    for cat in p.categories
                ]
                for p in product_controller.get_all()
            )
            if has_products:
                raise ValueError("Не може да изтриете категория с налични продукти!")
