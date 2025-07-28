from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional


class DocumentSignatureAudit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id")
    user_id: int = Field(foreign_key="user.id")
    role: str  # SigningRole as string
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: str  # e.g. "signed"
