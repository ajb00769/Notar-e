from pydantic import BaseModel
from datetime import datetime
from app.models.document import DocumentType
from app.enums.appointment_status import AppointmentStatus
from sqlmodel import Field


class AppointmentCreate(BaseModel):
    user_id: int = Field(foreign_key="users.id")
    doc_type: DocumentType
    scheduled_at: datetime


class AppointmentRead(AppointmentCreate):
    id: int
    status: AppointmentStatus
