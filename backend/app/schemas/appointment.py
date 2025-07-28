from pydantic import BaseModel
from datetime import datetime
from app.enums.document_types import DocumentType
from app.enums.appointment_status import AppointmentStatus


class AppointmentCreate(BaseModel):
    user_id: int
    doc_type: DocumentType
    scheduled_at: datetime


class AppointmentRead(AppointmentCreate):
    id: int
    status: AppointmentStatus
