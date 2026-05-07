import re


class UserValidator:
    @staticmethod
    def validate_user_data(username: str, password: str, email: str, role: str, status: str):
        """Основна валидация при регистрация или редакция. Запазваме всички изисквания."""

        # Валидация на потребителско име
        if not username or len(username.strip()) < 3:
            raise ValueError("Потребителското име трябва да е поне 3 символа.")
        if not username.isalnum():
            raise ValueError("Потребителското име може да съдържа само букви и цифри.")

        # Валидация на парола (преди хеширане)
        if len(password) < 6:
            raise ValueError("Паролата трябва да бъде поне 6 символа.")
        if password.isdigit() or password.isalpha():
            raise ValueError("Паролата трябва да съдържа комбинация от букви и цифри.")

        # Валидация на имейл
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValueError(f"Невалиден формат на имейл: {email}")

        # Валидация на системни константи
        UserValidator.validate_role(role)
        UserValidator.validate_status(status)

    @staticmethod
    def validate_role(role: str):
        """Проверка дали ролята е сред разрешените."""
        if role not in ["Admin", "Operator", "Anonymous"]:
            raise ValueError("Невалидна роля. Изберете: Admin, Operator или Anonymous.")

    @staticmethod
    def validate_status(status: str):
        """Проверка дали статусът е валиден."""
        if status not in ["Active", "Inactive"]:
            raise ValueError("Невалиден статус. Разрешени: Active / Inactive.")

    @staticmethod
    def validate_unique_username(username: str, controller):
        """Проверява дали името е заето."""
        if controller.get_by_username(username):
            raise ValueError(f"Потребителското име '{username}' вече е заето.")

    @staticmethod
    def validate_login(username: str, password: str, controller):
        """Проверка при влизане."""
        user = controller.get_by_username(username)
        if not user:
            raise ValueError("Грешно потребителско име или парола.")

        if user.status != "Active":
            raise ValueError("Този профил е деактивиран. Свържете се с администратор.")

        # Използваме вътрешния метод на контролера за проверка на хеша
        if not controller._check_password(user.password, password):
            raise ValueError("Грешно потребителско име или парола.")

        return user

    @staticmethod
    def confirm_admin(user):
        """Гарантира администраторски права за критични операции."""
        if not user or user.role != "Admin":
            raise PermissionError("Достъпът е отказан. Необходими са администраторски права.")

    @staticmethod
    def validate_not_self(current_user_username: str, target_user_username: str):
        if current_user_username.lower() == target_user_username.lower():
            raise ValueError("Не можете да деактивирате или триете собствения си профил!")

    @staticmethod
    def validate_not_last_admin(target_user, all_users):
        if target_user.role == "Admin" and target_user.status == "Active":
            # Броим колко АКТИВНИ администратори има, изключвайки този, когото искаме да променим
            active_admins = [ u for u in all_users if u.role == "Admin" and u.status == "Active" and
                              u.user_id != target_user.user_id]
            if not active_admins:
                raise ValueError("Операцията е отказана: Трябва да остане поне един активен администратор в системата.")