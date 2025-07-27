from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict
from datetime import date
from app.enums.document_status import DocumentStatus
from app.enums.document_types import DocumentType
from pydantic import field_validator
from app.schemas.signature import SignatureEntry
from app.enums.signing_roles import SigningRole


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

    @field_validator("signatures")
    def validate_signatures(cls, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError(
                "signatures must be a dict mapping role to signature entry"
            )
        seen_roles = set()
        allowed_roles = set(role.value for role in SigningRole)
        for role, entry in v.items():
            if not isinstance(role, str):
                raise ValueError("signature role keys must be strings")
            if role not in allowed_roles:
                raise ValueError(f"'{role}' is not an allowed signing role")
            if role in seen_roles:
                raise ValueError(
                    f"Duplicate signature for role '{role}' is not allowed"
                )
            seen_roles.add(role)
            if not isinstance(entry, dict):
                raise ValueError("signature entry must be a dict")
            # Validate required keys
            for key in ("user_id", "signature", "timestamp"):
                if key not in entry:
                    raise ValueError(
                        f"signature entry for role '{role}' missing key: {key}"
                    )
        return v
