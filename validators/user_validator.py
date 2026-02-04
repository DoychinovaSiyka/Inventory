import re


class UserValidator:


    @staticmethod
    def validate_username(username: str):
        if not username:
            raise ValueError("Потребителското име е задължително.")

        if len(username) < 3 or len(username) > 20:
            raise ValueError("Потребителското име трябва да е между 3 и 20 символа.")

        if " " in username:
            raise ValueError("Потребителското име не може да съдържа интервали.")

        return True


    #   PASSWORD (минимум 6 символа, хеширана)

    @staticmethod
    def validate_password(password: str):
        if not password:
            raise ValueError("Паролата е задължителна.")

        if len(password) < 6:
            raise ValueError("Паролата трябва да е поне 6 символа.")

        return True


    #   EMAIL ( валиден формат )

    @staticmethod
    def validate_email(email: str):
        if not email:
            raise ValueError("Имейлът е задължителен.")

        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(pattern, email):
            raise ValueError("Невалиден имейл адрес.")

        return True


    #   ROLE (SRS: Admin, Operator, Anonymous)
    @staticmethod
    def validate_role(role: str):
        valid_roles = ["Admin", "Operator", "Anonymous"]
        if role not in valid_roles:
            raise ValueError(f"Невалидна роля. Позволени роли: {valid_roles}")

        return True



    #   STATUS (SRS: Active, Disabled)
    @staticmethod
    def validate_status(status: str):
        valid_status = ["Active", "Disabled"]
        if status not in valid_status:
            raise ValueError("Статусът трябва да бъде 'Active' или 'Disabled'.")

        return True


    #   ПЪЛНА ВАЛИДАЦИЯ НА ПОТРЕБИТЕЛ

    @staticmethod
    def validate_user_data(username, password, email, role, status):
        UserValidator.validate_username(username)
        UserValidator.validate_password(password)
        UserValidator.validate_email(email)
        UserValidator.validate_role(role)
        UserValidator.validate_status(status)
        return True
