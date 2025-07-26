from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional
from datetime import date
from app.enums.document_status import DocumentStatus
from app.enums.document_types import DocumentType


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    doc_type: DocumentType
    status: DocumentStatus = DocumentStatus.PENDING
    uploaded_by: str
    upload_date: date
    blob_uri: str
    document_hash: str
    signatures: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSONB))
