import re


class UserValidator:

    # USERNAME
    @staticmethod
    def validate_username(username: str):
        if not username or not str(username).strip():
            raise ValueError("Потребителското име е задължително.")

        clean_username = str(username).strip()
        if len(clean_username) < 3 or len(clean_username) > 20:
            raise ValueError("Потребителското име трябва да е между 3 и 20 символа.")

        if " " in clean_username:
            raise ValueError("Потребителското име не може да съдържа интервали.")

        return clean_username

    # PASSWORD (минимум 6 символа)
    @staticmethod
    def validate_password(password: str):
        if not password:
            raise ValueError("Паролата е задължителна.")

        if len(str(password)) < 6:
            raise ValueError("Паролата трябва да е поне 6 символа.")

        return password  # Паролата не я тримваме, защото интервалите може да са част от нея

    # EMAIL (валиден формат)
    @staticmethod
    def validate_email(email: str):
        if not email:
            raise ValueError("Имейлът е задължителен.")

        clean_email = str(email).strip().lower()
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

        if not re.match(pattern, clean_email):
            raise ValueError("Невалиден имейл адрес.")

        return clean_email

    # ROLE (Admin, Operator, Anonymous)
    @staticmethod
    def validate_role(role: str):
        valid_roles = ["Admin", "Operator", "Anonymous"]
        clean_role = str(role).strip()

        if clean_role not in valid_roles:
            raise ValueError(f"Невалидна роля. Позволени роли: {valid_roles}")

        return clean_role

    # STATUS (Active, Disabled, Inactive)
    @staticmethod
    def validate_status(status: str):
        # Добавихме 'Inactive', тъй като го ползваш в контролера
        valid_status = ["Active", "Disabled", "Inactive"]
        clean_status = str(status).strip()

        if clean_status not in valid_status:
            raise ValueError(f"Невалиден статус. Позволени: {valid_status}")

        return clean_status

    # ГРУПОВА ВАЛИДАЦИЯ
    @staticmethod
    def validate_user_data(username, password, email, role, status):
        UserValidator.validate_username(username)
        UserValidator.validate_password(password)
        UserValidator.validate_email(email)
        UserValidator.validate_role(role)
        UserValidator.validate_status(status)
        return True

    # ПРОВЕРКА ЗА АДМИН
    @staticmethod
    def confirm_admin(user):
        """ Проверява дали потребителят има администраторски права. """
        if not user or str(user.role) != "Admin":
            raise PermissionError("Тази операция е достъпна само за администратори.")
        return True

    # ЗАЩИТА ОТ САМОУНИЩОЖЕНИЕ
    @staticmethod
    def validate_not_self(acting_username, target_username):
        """ Предотвратява админ да деактивира/изтрие себе си. """
        if str(acting_username) == str(target_username):
            raise ValueError("Не можете да извършите тази операция върху собствения си акаунт.")
        return True