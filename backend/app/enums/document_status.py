from enum import Enum

class DocumentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ACTION_REQUIRED = "action_required"