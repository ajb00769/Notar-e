from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AppointmentCreate(BaseModel):
    user_id: int
    doc_type: str
    scheduled_at: datetime


class AppointmentRead(AppointmentCreate):
    id: int
    status: str
