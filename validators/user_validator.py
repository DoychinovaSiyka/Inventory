import re


class UserValidator:
    @staticmethod
    def validate_user_data(username: str, password: str, email: str, role: str, status: str):
        """ Основна валидация при регистрация или редакция. """
        if not username or len(username.strip()) < 3:
            raise ValueError("Потребителското име трябва да е поне 3 символа.")

        # Проверка за сила на паролата
        if len(password) < 6:
            raise ValueError("Паролата трябва да бъде поне 6 символа.")
        if password.isdigit() or password.isalpha():
            raise ValueError("Паролата трябва да съдържа и букви, и цифри.")

        # Проверка на имейл формат
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValueError(f"Невалиден формат на имейл: {email}")

        # Проверка за валидна роля и статус
        if role not in ["Admin", "Operator", "Anonymous"]:
            raise ValueError("Невалидна роля на потребител.")

        allowed_statuses = ["Active", "Inactive", "Blocked"]
        if status not in allowed_statuses:
            raise ValueError(f"Невалиден статус. Позволени: {', '.join(allowed_statuses)}")

    @staticmethod
    def confirm_admin(user):
        """ Проверка дали потребителят има права за административни действия. """
        if not user or user.role != "Admin":
            raise PermissionError("Действието изисква администраторски права!")

    @staticmethod
    def validate_not_self(current_user_username: str, target_username: str):
        """ Предотвратява самонараняване (триене на собствения профил). """
        if current_user_username == target_username:
            raise ValueError("Не можете да извършите това действие върху собствения си профил!")

    @staticmethod
    def validate_not_last_admin(target_user, all_users):
        """ Критична проверка: Предотвратява премахването на последния админ. """
        if target_user.role == "Admin":
            admins = [u for u in all_users if u.role == "Admin"]
            if len(admins) <= 1:
                raise ValueError("Критична грешка: Не можете да премахнете последния администратор в системата!")