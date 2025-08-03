from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional
from app.enums.signing_roles import SigningRole
from enum import IntEnum


class AuditActions(IntEnum):
    SIGNED = 1


class DocumentSignatureAudit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    user_id: int = Field(foreign_key="users.id")
    role: SigningRole
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: AuditActions
