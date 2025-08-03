from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone
from app.enums.appointment_status import AppointmentStatus
from app.models.document import DocumentType


class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None, primary_key=True
    )  # optional and None for object creation/new write
    user_id: int = Field(nullable=False, foreign_key="users.id")
    doc_type: DocumentType
    scheduled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: AppointmentStatus = AppointmentStatus.PENDING
