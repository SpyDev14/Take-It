from enum import Enum
import json

class WorkMode(Enum):
    RECIPIENT: int = 0
    SENDER: int = 1

class Info:
    def __init__(self, user_name: str, work_mode: WorkMode):
        self.user_name: str = user_name
        self.work_mode: WorkMode = work_mode