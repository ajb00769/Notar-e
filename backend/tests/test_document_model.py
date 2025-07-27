import pydantic
import pytest
from app.models.document import Document
from app.enums.document_status import DocumentStatus
from app.enums.document_types import DocumentType
from app.enums.signing_roles import SigningRole
from datetime import date

# Valid minimal document data
base_doc = dict(
    name="TestDoc",
    doc_type=DocumentType.AFFIDAVIT,
    status=DocumentStatus.PENDING,
    uploaded_by=1,
    upload_date=date.today(),
    blob_uri="s3://bucket/key",
    document_hash="abc123",
)


def test_signatures_valid():
    doc = Document(
        **base_doc,
        signatures={
            SigningRole.NOTARY.value: {
                "user_id": 1,
                "signature": "sig",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        },
    )
    assert doc.signatures[SigningRole.NOTARY.value]["user_id"] == 1


def test_signatures_none():
    doc = Document(**base_doc, signatures=None)
    assert doc.signatures == {}


def test_signatures_invalid_type():
    with pytest.raises(pydantic.ValidationError):
        Document(**base_doc, signatures=[1, 2, 3])


def test_signatures_missing_key():
    with pytest.raises(pydantic.ValidationError):
        Document(
            **base_doc,
            signatures={
                SigningRole.NOTARY.value: {"user_id": 1, "signature": "sig"}
            },  # missing timestamp
        )


def test_signatures_duplicate_role():
    # Not possible in a dict, but test for code path
    doc = Document(
        **base_doc,
        signatures={
            SigningRole.NOTARY.value: {
                "user_id": 1,
                "signature": "sig",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        },
    )
    # No error, as dict can't have duplicate keys
    assert SigningRole.NOTARY.value in doc.signatures


def test_signatures_disallowed_role():
    with pytest.raises(pydantic.ValidationError):
        Document(
            **base_doc,
            signatures={
                "INVALID_ROLE": {
                    "user_id": 1,
                    "signature": "sig",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
            },
        )
