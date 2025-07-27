import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services import document_service
from app.enums.document_types import DocumentType
from app.enums.document_status import DocumentStatus
from app.enums.signing_roles import SigningRole


@pytest.mark.asyncio
@patch("app.services.storage_service.upload_to_s3")
@patch(
    "app.services.storage_service.generate_presigned_get_url",
    return_value="https://mocked-s3-url",
)
@patch("app.services.storage_service.delete_from_s3")
async def test_create_document_entry_success(mock_delete, mock_presign, mock_upload):
    # Minimal doc_data mock
    doc_data = MagicMock()
    doc_data.uploaded_by = 1
    doc_data.date = "2024-01-01"
    doc_data.name = "test.pdf"
    doc_data.doc_type = "AFFIDAVIT"
    doc_data.status = "PENDING"
    doc_data.signatures = {}
    doc_data.signed_blob_uri = None
    doc_data.signed_document_hash = None
    doc_data.document_hash = "abc123"
    s3_key = "test-key"
    session = AsyncMock()
    # Patch DocumentModel
    with patch("app.services.document_service.DocumentModel") as MockDocModel:
        instance = MockDocModel.return_value
        instance.id = 42
        instance.uploaded_by = 1
        instance.name = "test.pdf"
        instance.doc_type = "AFFIDAVIT"
        instance.status = "PENDING"
        instance.signatures = {}
        instance.upload_date = "2024-01-01"
        instance.blob_uri = "s3://your-s3-bucket/test-key"
        instance.document_hash = "abc123"
        instance.signed_blob_uri = None
        instance.signed_document_hash = None
        session.add = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        result = await document_service.create_document_entry(doc_data, s3_key, session)
        assert result["id"] == 42
        assert result["blob_uri"].startswith("s3://")
        mock_upload.assert_not_called()  # upload is not called in this function
        mock_presign.assert_called_once_with(s3_key)


@pytest.mark.asyncio
@patch("app.services.storage_service.delete_from_s3")
async def test_create_document_entry_cleanup_on_error(mock_delete):
    # Simulate error after file_uploaded = True
    doc_data = MagicMock()
    doc_data.uploaded_by = 1
    doc_data.date = "2024-01-01"
    doc_data.name = "test.pdf"
    doc_data.doc_type = "AFFIDAVIT"
    doc_data.status = "PENDING"
    doc_data.signatures = {}
    doc_data.signed_blob_uri = None
    doc_data.signed_document_hash = None
    doc_data.document_hash = "abc123"
    s3_key = "test-key"
    session = MagicMock()
    with patch(
        "app.services.document_service.DocumentModel", side_effect=Exception("fail")
    ):
        with pytest.raises(Exception):
            await document_service.create_document_entry(doc_data, s3_key, session)
        mock_delete.assert_called_with(s3_key)


@pytest.mark.asyncio
@patch("app.services.document_service.get_document_with_signing_status")
async def test_check_document_completion_affidavit(mock_get_status):
    # Simulate a document with all required signatures for affidavit
    class DummyDoc:
        doc_type = DocumentType.AFFIDAVIT
        status = DocumentStatus.PENDING
        signed_by = [
            SigningRole.AFFIANT,
            SigningRole.NOTARY,
            SigningRole.WITNESS,
            SigningRole.GRANTOR,
            # Simulate two witnesses as witness_1 and witness_2
        ]

    dummy = DummyDoc()
    dummy.signed_by = [
        SigningRole.AFFIANT,
        SigningRole.NOTARY,
        SigningRole.GRANTOR,
        # witness_1 and witness_2 as string values
    ]
    # Add both witnesses as string keys
    dummy.signed_by.extend(
        [
            type("Enum", (), {"value": "witness_1"})(),
            type("Enum", (), {"value": "witness_2"})(),
        ]
    )
    mock_get_status = AsyncMock()
    mock_get_status.return_value = dummy
    session = AsyncMock()
    result = await document_service.check_document_completion(1, session)
    assert result["is_complete"] is True
    assert result["missing_signatures"] == []


@pytest.mark.asyncio
@patch("app.services.document_service.get_document_with_signing_status")
async def test_check_document_completion_deed_missing_grantee(mock_get_status):
    # Simulate a document with all but grantee signed for a deed
    class DummyDoc:
        doc_type = DocumentType.DEED
        status = DocumentStatus.PENDING
        signed_by = [
            SigningRole.NOTARY,
            SigningRole.GRANTOR,
            # witness_1 and witness_2 as string values
        ]

    dummy = DummyDoc()
    dummy.signed_by = [
        SigningRole.NOTARY,
        SigningRole.GRANTOR,
        type("Enum", (), {"value": "witness_1"})(),
        type("Enum", (), {"value": "witness_2"})(),
    ]
    mock_get_status.return_value = dummy
    session = AsyncMock()
    result = await document_service.check_document_completion(2, session)
    assert result["is_complete"] is False
    assert "grantee" in result["missing_signatures"]
