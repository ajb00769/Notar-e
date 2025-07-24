from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str
    doc_type: str
    scheduled_at: datetime
    status: str = "Pending"
