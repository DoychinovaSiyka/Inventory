import re
import uuid


class UserValidator:
    @staticmethod
    def validate_user_data(username: str, password: str, email: str, role: str, status: str):
        """Основна валидация при регистрация или редакция."""


        if not username or len(username.strip()) < 3:
            raise ValueError("Потребителското име трябва да е поне 3 символа.")
        if not username.isalnum():
            raise ValueError("Потребителското име може да съдържа само букви и цифри.")

        if len(password) < 6:
            raise ValueError("Паролата трябва да бъде поне 6 символа.")
        if password.isdigit() or password.isalpha():
            raise ValueError("Паролата трябва да съдържа комбинация от букви и цифри.")


        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValueError(f"Невалиден формат на имейл: {email}")

        UserValidator.validate_role(role)
        UserValidator.validate_status(status)

    @staticmethod
    def validate_role(role: str):
        if role not in ["Admin", "Operator", "Anonymous"]:
            raise ValueError("Невалидна роля. Изберете: Admin, Operator или Anonymous.")

    @staticmethod
    def validate_status(status: str):
        if status not in ["Active", "Inactive"]:
            raise ValueError("Невалиден статус. Разрешени: Active / Inactive.")

    @staticmethod
    def validate_exists(username: str, controller):
        """Търсене по потребителско име."""
        user = controller.get_by_username(username)
        if not user:
            raise ValueError(f"Потребител '{username}' не е намерен.")
        return user

    @staticmethod
    def validate_exists_by_id(user_id, controller):
        """Позволява търсене по кратко ID (8 символа) или пълно ID."""
        user = controller.get_by_id(str(user_id).strip())
        if not user:
            raise ValueError(f"Потребител с ID '{user_id}' не съществува.")
        return user

    @staticmethod
    def validate_unique_username(username: str, controller, exclude_username=None):
        """Проверява дали потребителското име е свободно."""
        if username == exclude_username:
            return
        if controller.get_by_username(username):
            raise ValueError(f"Потребителското име '{username}' вече е заето.")

    @staticmethod
    def validate_login(username: str, password: str, controller):
        """Проверка при влизане в системата."""
        user = controller.get_by_username(username)
        if not user:
            raise ValueError("Грешно потребителско име или парола.")

        if user.status != "Active":
            raise ValueError("Този профил е деактивиран. Свържете се с администратор.")

        if not controller._check_password(user.password, password):
            raise ValueError("Грешно потребителско име или парола.")

        return user

    @staticmethod
    def confirm_admin(user):
        """Проверка за администраторски достъп."""
        if not user or user.role != "Admin":
            raise PermissionError("Достъпът е отказан. Необходими са администраторски права.")

    @staticmethod
    def validate_not_self(current_user_username: str, target_username: str):
        """Предотвратява действия върху собствения профил."""
        if current_user_username == target_username:
            raise ValueError("Не можете да променяте или триете собствения си профил от това меню.")

    @staticmethod
    def validate_not_last_admin(target_user, all_users):
        """Гарантира, че винаги остава поне един активен администратор."""
        if target_user.role == "Admin":
            admin_count = sum(1 for u in all_users if u.role == "Admin" and u.status == "Active")
            if admin_count <= 1:
                raise ValueError("Не можете да премахнете или деактивирате последния активен администратор.")
