from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict
from datetime import date
from app.enums.document_status import DocumentStatus
from app.enums.document_types import DocumentType
from pydantic import BaseModel, validator
from datetime import datetime


class SignatureEntry(BaseModel):
    user_id: int
    signature: str
    timestamp: datetime  # ISO8601 string, enforced by Pydantic


# Signatures is a mapping from role (as string, e.g. "notary") to SignatureEntry
# Example:
# signatures = {
#     "notary": {"user_id": 123, "signature": "base64...", "timestamp": "2024-06-01T12:34:56Z"},
#     "affiant": {"user_id": 456, "signature": "base64...", "timestamp": "2024-06-01T12:35:56Z"}
# }


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
    uploaded_by: int = Field(foreign_key="user.id")
    upload_date: date
    blob_uri: str
    document_hash: str
    signatures: Optional[Dict[str, SignatureEntry]] = Field(
        default_factory=dict, sa_column=Column(JSONB)
    )

    @validator("signatures", pre=True, always=True)
    def validate_signatures(cls, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError(
                "signatures must be a dict mapping role to signature entry"
            )
        for role, entry in v.items():
            if not isinstance(role, str):
                raise ValueError("signature role keys must be strings")
            if not isinstance(entry, dict):
                raise ValueError("signature entry must be a dict")
            # Validate required keys
            for key in ("user_id", "signature", "timestamp"):
                if key not in entry:
                    raise ValueError(
                        f"signature entry for role '{role}' missing key: {key}"
                    )
        return v
