from typing import Optional, List
from models.user import User
from validators.user_validator import UserValidator
from controllers.abstract_controller import AbstractController


class UserController(AbstractController):
    """Управлява потребителите, автентикацията, ролите и статусите."""

    def __init__(self, repo):
        self.logged_user: Optional[User] = None
        super().__init__(repo)

        # Зареждаме потребителите
        self.users = self.load() or []

        # Създаваме системните потребители, ако липсват
        if not self.get_by_username("admin"):
            self._create_default_admin()
        if not self.get_by_username("operator"):
            self._create_default_operator()

    #  Мапване dict <-> User
    def from_dict(self, data):
        return User.from_dict(data)

    def to_dict(self, obj):
        return obj.to_dict()

    def save_users(self):
        self.save(self.users)

    def find_user_flexible(self, identifier: str) -> Optional[User]:
        if not identifier:
            return None
        identifier = str(identifier).strip()
        user = self.get_by_id(identifier)
        if user:
            return user
        return self.get_by_username(identifier)



    def _hash_password(self, password: str) -> str:
        if not password:
            return ""
        return "".join(str(ord(c)) for c in password)



    def _check_password(self, stored_password_hash: str, provided_password: str) -> bool:
        return stored_password_hash == self._hash_password(provided_password)



    def is_admin(self, user):
        if not user:
            return False
        return str(user.role).lower() == "admin"




    def get_by_username(self, username: str) -> Optional[User]:
        if not username:
            return None

        username = username.strip().lower()
        for u in self.users:
            if u.username.lower() == username:
                return u
        return None


    def get_all(self):
        return self.users



    def get_by_id(self, user_id: str) -> Optional[User]:
        uid = str(user_id or "").strip()
        if not uid:
            return None

        for u in self.users:
            full_id = str(u.user_id)
            short_id = full_id[:8]

            if uid == short_id or uid == full_id:
                return u

        return None




    def login(self, username: str, password: str) -> Optional[User]:
        user = UserValidator.validate_login(username, password, self)
        if user:
            self.logged_user = user
            return user
        return None



    def register(self, first_name, last_name, email, username, password, role="Operator"):
        UserValidator.validate_user_data(username, password, email, role, "Active")
        UserValidator.validate_unique_username(username, self)

        new_user = User(user_id=None, first_name=first_name.strip(),last_name=last_name.strip(), email=email.strip(),
                        username=username.strip().lower(), password=self._hash_password(password),
                        role=role, status="Active")

        self.users.append(new_user)
        self.save_users()
        return new_user




    def change_role(self, identifier, new_role):
        user = self.find_user_flexible(identifier)
        if not user:
            raise ValueError(f"Потребител '{identifier}' не е намерен.")

        UserValidator.validate_role(new_role)

        if user.role == new_role:
            raise ValueError(f"Потребителят вече е с роля '{new_role}'.")

        user.role = new_role
        user.update_modified()
        self.save_users()



    def change_status(self, acting_user: User, identifier: str, new_status: str):
        user = self.find_user_flexible(identifier)
        if not user:
            raise ValueError(f"Потребител '{identifier}' не е намерен.")

        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_status(new_status)
        UserValidator.validate_not_self(acting_user.username, user.username)

        user.status = new_status
        user.update_modified()
        self.save_users()
        return True




    def delete_user(self, acting_user: User, identifier: str):
        user = self.find_user_flexible(identifier)
        if not user:
            raise ValueError(f"Потребител '{identifier}' не е намерен.")

        UserValidator.confirm_admin(acting_user)
        UserValidator.validate_not_self(acting_user.username, user.username)
        UserValidator.validate_not_last_admin(user, self.users)

        self.users.remove(user)
        self.save_users()
        return True




    def _create_default_admin(self):
        admin = User(user_id=None, first_name="Admin", last_name="System", email="admin@system.local",
                     username="admin", password=self._hash_password("admin123"), role="Admin", status="Active")
        self.users.append(admin)
        self.save_users()



    def _create_default_operator(self):
        operator = User(user_id=None, first_name="Operator", last_name="User",
                        email="operator@example.com", username="operator", password=self._hash_password("operator123"),
                        role="Operator", status="Active")
        self.users.append(operator)
        self.save_users()




    def validate_field(self, field_type: str, value: str) -> Optional[str]:
        try:
            if field_type == "username":
                UserValidator.validate_unique_username(value, self)
                if not value or len(value.strip()) < 3:
                    raise ValueError("Потребителското име трябва да е поне 3 символа.")
                if not value.isalnum():
                    raise ValueError("Потребителското име може да съдържа само букви и цифри.")

            elif field_type == "email":
                UserValidator.validate_user_data(username="tmp_valid", password="Valid123Password",
                                                 email=value, role="Operator", status="Active")

            elif field_type == "password":

                UserValidator.validate_user_data(username="tmp_valid", password=value,
                                                 email="tmp@email.com", role="Operator", status="Active")

            elif field_type == "role":
                UserValidator.validate_role(value)

            return None

        except ValueError as e:
            return str(e)