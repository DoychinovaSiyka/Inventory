import datetime
import uuid

class UserActivityLog:
    def __init__(self,user_id,action,details = ""):
        self.log_id = str(uuid.uuid4())
        self.user_id = user_id
        self.action = action
        self.details = details
        self.timestamp - datetime.datetime.now().strftime("%Y-%m0%d %H:%M:%S")


    def to_dict(self):
        return {
            "log_id": self.log_id,
            "user_id": self.user_id,
            "action":self.action,
            "details": self.details,
            "timestamp":self.timestamp
        }

    