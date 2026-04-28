import re


class UserValidator:
    @staticmethod
    def validate_user_data(username: str, password: str, email: str, role: str, status: str):
        """ Основна валидация при регистрация или редакция. """
        if not username or len(username.strip()) < 3:
            raise ValueError("Потребителското име трябва да е поне 3 символа.")

        if len(password) < 6:
            raise ValueError("Паролата трябва да бъде поне 6 символа.")
        if password.isdigit() or password.isalpha():
            raise ValueError("Паролата трябва да съдържа и букви, и цифри.")

        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValueError(f"Невалиден формат на имейл: {email}")
        UserValidator.validate_role(role)
        UserValidator.validate_status(status)

    @staticmethod
    def validate_role(role: str):
        """ Проверка за валидна роля. """
        if role not in ["Admin", "Operator", "Anonymous"]:
            raise ValueError("Невалидна роля на потребител.")

    @staticmethod
    def validate_status(status: str):
        """ Валидация при промяна на статус. """
        if status not in ["Active", "Inactive"]:
            raise ValueError("Невалиден статус. Разрешени: Active / Inactive.")

    @staticmethod
    def validate_exists(username: str, controller):
        """ Проверява дали потребителят съществува. """
        user = controller.get_by_username(username)
        if not user:
            raise ValueError("Потребителят не е намерен.")
        return user

    @staticmethod
    def validate_unique_username(username: str, controller):
        """ Проверява дали потребителското име вече съществува. """
        if controller.get_by_username(username):
            raise ValueError("Потребителското име вече съществува.")

    @staticmethod
    def validate_login(username: str, password: str, controller):
        """ Проверка при логин. """
        user = controller.get_by_username(username)
        if not user:
            raise ValueError("Невалидно потребителско име или парола.")
        if user.status != "Active":
            raise ValueError("Потребителят е деактивиран.")

        # Проверка на паролата - хеширана
        if user.password != controller._hash_password(password):
            raise ValueError("Невалидно потребителско име или парола.")
        return user

    @staticmethod
    def confirm_admin(user):
        """ Проверка дали потребителят има права за административни действия. """
        if not user or user.role != "Admin":
            raise PermissionError("Действието изисква администраторски права!")

    @staticmethod
    def validate_not_self(current_user_username: str, target_username: str):
        """ Предотвратява действия върху собствения профил. """
        if current_user_username == target_username:
            raise ValueError("Не можете да извършите това действие върху собствения си профил!")

    @staticmethod
    def validate_not_last_admin(target_user, all_users):
        """ Предотвратява премахването на последния администратор. """
        if target_user.role == "Admin":
            admin_count = sum(1 for u in all_users if u.role == "Admin")
            if admin_count <= 1:
                raise ValueError("Не можете да премахнете последния администратор в системата!")
