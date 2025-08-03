from enum import IntEnum, StrEnum
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone


class DocumentStatus(IntEnum):
    PENDING = 1
    COMPLETED = 2
    ACTION_REQUIRED = 9
    CANCELLED = 0


class DocumentType(StrEnum):
    AFFIDAVIT = "affidavit"
    DEED = "deed"
    CONTRACT = "contract"
    POWER_OF_ATTORNEY = "power_of_attorney"


class Document(SQLModel, table=True):
    """
    signatures: Dict[str, SignatureEntry]
    - Key: role as string (e.g., "notary", "affiant")
    - Value: SignatureEntry (user_id, signature, timestamp)
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    doc_type: DocumentType
    status: DocumentStatus = DocumentStatus.PENDING
    uploaded_by: int = Field(foreign_key="users.id")
    upload_date: datetime = datetime.now(timezone.utc)
    blob_uri: str
    document_hash: str
    signed_blob_uri: Optional[str] = None  # S3 URI of the signed PDF
    signed_document_hash: Optional[str] = None  # Hash of the signed PDF


class DocumentSignature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    document_id: int = Field(foreign_key="document.id")
    signature: Optional[str]
    timestamp: datetime
