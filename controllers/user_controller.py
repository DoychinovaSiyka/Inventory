from typing import Optional, List
from models.user import User
from validators.user_validator import UserValidator
from controllers.abstract_controller import AbstractController


class UserController(AbstractController):
    def __init__(self, repo):
        super().__init__(repo)
        self.users: List[User] = self.load() or []

    def from_dict(self, data):
        return User.from_dict(data)

    def to_dict(self, obj):
        return obj.to_dict()

    def _save(self):
        self.save(self.users)



    def get_all(self) -> List[User]:
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

    def get_by_username(self, username: str) -> Optional[User]:
        if not username:
            return None

        username = username.strip().lower()
        for u in self.users:
            if u.username.lower() == username:
                return u
        return None



    def _hash_password(self, password: str) -> str:
        return "".join(str(ord(c)) for c in password)

    def _check_password(self, stored_hash: str, provided_password: str) -> bool:
        return stored_hash == self._hash_password(provided_password)


    def login(self, username: str, password: str) -> Optional[User]:
        user = UserValidator.validate_login(username, password, self)
        return user



    def register(self, first_name, last_name, email, username, password, role="Operator"):
        UserValidator.validate_user_data(username, password, email, role, "Active")
        UserValidator.validate_unique_username(username, self)

        new_user = User(
            user_id=None,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.strip(),
            username=username.strip().lower(),
            password=self._hash_password(password),
            role=role,
            status="Active"
        )

        self.users.append(new_user)
        self._save()
        return new_user



    def change_role(self, acting_user: User, identifier: str, new_role: str):
        UserValidator.confirm_admin(acting_user)

        user = self.get_by_username(identifier) or self.get_by_id(identifier)
        if not user:
            raise ValueError(f"Потребител '{identifier}' не е намерен.")

        UserValidator.validate_role(new_role)
        UserValidator.validate_not_self(acting_user.username, user.username)

        if user.role == "Admin" and new_role != "Admin":
            UserValidator.validate_not_last_admin(user, self.users)

        user.role = new_role
        user.update_modified()
        self._save()
        return True


    def change_status(self, acting_user: User, identifier: str, new_status: str):
        UserValidator.confirm_admin(acting_user)

        user = self.get_by_username(identifier) or self.get_by_id(identifier)
        if not user:
            raise ValueError(f"Потребител '{identifier}' не е намерен.")

        UserValidator.validate_status(new_status)
        UserValidator.validate_not_self(acting_user.username, user.username)

        user.status = new_status
        user.update_modified()
        self._save()
        return True



    def delete_user(self, acting_user: User, identifier: str):
        UserValidator.confirm_admin(acting_user)

        user = self.get_by_username(identifier) or self.get_by_id(identifier)
        if not user:
            raise ValueError(f"Потребител '{identifier}' не е намерен.")

        UserValidator.validate_not_self(acting_user.username, user.username)
        UserValidator.validate_not_last_admin(user, self.users)

        self.users.remove(user)
        self._save()
        return True



    def validate_field(self, field_type: str, value: str) -> Optional[str]:
        try:
            if field_type == "username":
                UserValidator.validate_unique_username(value, self)
                if not value or len(value.strip()) < 3:
                    raise ValueError("Потребителското име трябва да е поне 3 символа.")
                if not value.isalnum():
                    raise ValueError("Потребителското име може да съдържа само букви и цифри.")

            elif field_type == "email":
                UserValidator.validate_email(value)

            elif field_type == "password":
                UserValidator.validate_user_data(
                    username="tmp_valid",
                    password=value,
                    email="tmp@email.com",
                    role="Operator",
                    status="Active"
                )

            elif field_type == "role":
                UserValidator.validate_role(value)

            return None

        except ValueError as e:
            return str(e)
