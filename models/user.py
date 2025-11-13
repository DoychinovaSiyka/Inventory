

import uuid
from datetime import datetime


class User:
    def __init__(self,user_id = None,first_name = "",last_name = "",email = "",username ="",password = "",role = "operator",status = "active",metadata = None,actions = None,created = None, modified =None):
        self.user_id = user_id if user_id else str(uuid.uuid4())
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password = password
        self.role = role  # администратор или админ да бъде ролята
        self.status = status # active,inactive , suspended
        self.metadata = metadata if metadata else {}
        self.actions = actions if actions else []
        self.created = created if created else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.modified = modified if modified else datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    def to_dict(self):
        return {
            "user_id": self.user_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "status": self.status,
            "metadata": self.metadata,
            "actions": self.actions,
            "created": self.created,
            "modified": self.modified
        }
    @staticmethod
    def deserialize():
        return Supplier(user_id=date.get("user_id"),
                        first_name=data.get("first_name"),
                        last_name=data.get("last_name"),
                        email=data.get("email"),
                        username=data.get("username"),
                        password=data.get("password"),
                        role = data.get("role","operator"),
                        status = data.get("status","active"),
                        metadata =  data.get("metadata",{}),
                        actions = data.get("actions",[]),
                        created = data.get("created"),
                        modified =data.get("modified"))



