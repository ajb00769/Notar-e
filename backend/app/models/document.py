import pydantic
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Dict, Any
from datetime import date
from app.enums.document_status import DocumentStatus
from app.enums.document_types import DocumentType
from pydantic import field_validator, model_validator
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
    signed_blob_uri: Optional[str] = None  # S3 URI of the signed PDF
    signed_document_hash: Optional[str] = None  # Hash of the signed PDF
    signatures: Optional[Dict[str, Any]] = Field(
        default_factory=dict, sa_column=Column(JSONB)
    )

    # Constructor to ensure that an empty dict is assigned to "signatures" if None is explicitly passed
    def __init__(self, **data):
        if "signatures" in data and data["signatures"] is None:
            data["signatures"] = {}
        super().__init__(**data)

    @classmethod
    @field_validator("signatures", mode="before")
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

    @model_validator(mode="after")
    def check_signatures(self):
        v = self.signatures
        if v is None:
            return self
        if not isinstance(v, dict):
            raise pydantic.ValidationError(
                "signatures must be a dict mapping role to signature entry"
            )
        seen_roles = set()
        allowed_roles = set(role.value for role in SigningRole)
        for role, entry in v.items():
            if not isinstance(role, str):
                raise pydantic.ValidationError("signature role keys must be strings")
            if role not in allowed_roles:
                raise pydantic.ValidationError(
                    f"'{role}' is not an allowed signing role"
                )
            if role in seen_roles:
                raise pydantic.ValidationError(
                    f"Duplicate signature for role '{role}' is not allowed"
                )
            seen_roles.add(role)
            if not isinstance(entry, dict):
                raise pydantic.ValidationError("signature entry must be a dict")
            for key in ("user_id", "signature", "timestamp"):
                if key not in entry:
                    raise ValueError(
                        f"signature entry for role '{role}' missing key: {key}"
                    )
        return self
