import re


class UserValidator:

    # ---------------------------------------------------------
    # ПЪЛНА ВАЛИДАЦИЯ ПРИ РЕГИСТРАЦИЯ
    # ---------------------------------------------------------
    @staticmethod
    def validate_user_data(username: str, password: str, email: str, role: str, status: str):

        # Username
        if not username or len(username.strip()) < 3:
            raise ValueError("Потребителското име трябва да е поне 3 символа.")
        if not username.isalnum():
            raise ValueError("Потребителското име може да съдържа само букви и цифри.")

        # Password
        if len(password) < 6:
            raise ValueError("Паролата трябва да бъде поне 6 символа.")
        if password.isdigit() or password.isalpha():
            raise ValueError("Паролата трябва да съдържа комбинация от букви и цифри.")

        # Email
        UserValidator.validate_email(email)

        # Role & Status
        UserValidator.validate_role(role)
        UserValidator.validate_status(status)

    # ---------------------------------------------------------
    # ОТДЕЛНА ВАЛИДАЦИЯ НА ИМЕЙЛ (за validate_field)
    # ---------------------------------------------------------
    @staticmethod
    def validate_email(email: str):
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email):
            raise ValueError(f"Невалиден формат на имейл: {email}")

    # ---------------------------------------------------------
    # РОЛЯ
    # ---------------------------------------------------------
    @staticmethod
    def validate_role(role: str):
        if role not in ["Admin", "Operator", "Anonymous"]:
            raise ValueError("Невалидна роля. Изберете: Admin, Operator или Anonymous.")

    # ---------------------------------------------------------
    # СТАТУС
    # ---------------------------------------------------------
    @staticmethod
    def validate_status(status: str):
        if status not in ["Active", "Inactive"]:
            raise ValueError("Невалиден статус. Разрешени: Active / Inactive.")

    # ---------------------------------------------------------
    # УНИКАЛНО ПОТРЕБИТЕЛСКО ИМЕ
    # ---------------------------------------------------------
    @staticmethod
    def validate_unique_username(username: str, controller):
        if controller.get_by_username(username):
            raise ValueError(f"Потребителското име '{username}' вече е заето.")

    # ---------------------------------------------------------
    # ЛОГИН
    # ---------------------------------------------------------
    @staticmethod
    def validate_login(username: str, password: str, controller):
        user = controller.get_by_username(username)
        if not user:
            raise ValueError("Грешно потребителско име или парола.")

        if user.status != "Active":
            raise ValueError("Този профил е деактивиран. Свържете се с администратор.")

        if not controller._check_password(user.password, password):
            raise ValueError("Грешно потребителско име или парола.")

        return user

    # ---------------------------------------------------------
    # АДМИН ПРАВА
    # ---------------------------------------------------------
    @staticmethod
    def confirm_admin(user):
        if not user or user.role != "Admin":
            raise PermissionError("Достъпът е отказан. Необходими са администраторски права.")

    # ---------------------------------------------------------
    # ЗАБРАНА ЗА ДЕЙСТВИЕ ВЪРХУ СЕБЕ СИ
    # ---------------------------------------------------------
    @staticmethod
    def validate_not_self(current_user_username: str, target_user_username: str):
        if current_user_username.lower() == target_user_username.lower():
            raise ValueError("Не можете да деактивирате или триете собствения си профил!")

    # ---------------------------------------------------------
    # ЗАБРАНА ЗА ИЗТРИВАНЕ НА ПОСЛЕДНИЯ АКТИВЕН АДМИН
    # ---------------------------------------------------------
    @staticmethod
    def validate_not_last_admin(target_user, all_users):
        if target_user.role == "Admin" and target_user.status == "Active":
            active_admins = [
                u for u in all_users
                if u.role == "Admin" and u.status == "Active" and u.user_id != target_user.user_id
            ]
            if not active_admins:
                raise ValueError("Операцията е отказана: Трябва да остане поне един активен администратор в системата.")
