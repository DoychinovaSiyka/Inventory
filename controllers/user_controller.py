from models.user import User
from repository.json_repository import  JSONRepository
from typing import Optional

class UserController:
    def __init__(self, user_repo):
        self.user_repo = user_repo
        self.logged_user: Optional[User] = None



