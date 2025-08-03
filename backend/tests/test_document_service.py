from datetime import datetime

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.services import document_service
from app.models.document import DocumentStatus, DocumentType
from app.schemas.signature import SignatureEntry


# @pytest.mark.asyncio
# @patch("app.services.storage_service.upload_to_s3")
# @patch(
#     "app.services.storage_service.generate_presigned_get_url",
#     return_value="https://mocked-s3-url",
# )
# @patch("app.services.storage_service.delete_from_s3")
# async def test_create_document_entry_success(mock_delete, mock_presign, mock_upload):
#     # Minimal doc_data mock
#     doc_data = MagicMock()
#     doc_data.uploaded_by = 1
#     doc_data.date = "2024-01-01"
#     doc_data.name = "test.pdf"
#     doc_data.doc_type = "AFFIDAVIT"
#     doc_data.status = "PENDING"
#     doc_data.signatures = {}
#     doc_data.signed_blob_uri = None
#     doc_data.signed_document_hash = None
#     doc_data.document_hash = "abc123"
#     s3_key = "test-key"
#     session = AsyncMock()
#     # Patch DocumentModel
#     with patch("app.services.document_service.DocumentModel") as MockDocModel:
#         instance = MockDocModel.return_value
#         instance.id = 42
#         instance.uploaded_by = 1
#         instance.name = "test.pdf"
#         instance.doc_type = "AFFIDAVIT"
#         instance.status = "PENDING"
#         instance.signatures = {}
#         instance.upload_date = "2024-01-01"
#         instance.blob_uri = "s3://your-s3-bucket/test-key"
#         instance.document_hash = "abc123"
#         instance.signed_blob_uri = None
#         instance.signed_document_hash = None
#         session.add = MagicMock()
#         session.commit = AsyncMock()
#         session.refresh = AsyncMock()
#         result = await document_service.create_document_entry(doc_data, s3_key, session)
#         assert result["id"] == 42
#         assert result["blob_uri"].startswith("s3://")
#         mock_upload.assert_not_called()  # upload is not called in this function
#         mock_presign.assert_called_once_with(s3_key)
#
#
# @pytest.mark.asyncio
# @patch("app.services.storage_service.delete_from_s3")
# async def test_create_document_entry_cleanup_on_error(mock_delete):
#     # Simulate error after file_uploaded = True
#     doc_data = MagicMock()
#     doc_data.uploaded_by = 1
#     doc_data.date = "2024-01-01"
#     doc_data.name = "test.pdf"
#     doc_data.doc_type = "AFFIDAVIT"
#     doc_data.status = "PENDING"
#     doc_data.signatures = {}
#     doc_data.signed_blob_uri = None
#     doc_data.signed_document_hash = None
#     doc_data.document_hash = "abc123"
#     s3_key = "test-key"
#     session = AsyncMock()
#     with patch(
#         "app.services.document_service.DocumentModel", side_effect=Exception("fail")
#     ):
#         with pytest.raises(Exception):
#             await document_service.create_document_entry(doc_data, s3_key, session)
#         mock_delete.assert_called_with(s3_key)


@pytest.mark.asyncio
@patch("app.services.document_service.update_document_status")
@patch("app.services.document_service.get_document_by_id")
async def test_check_document_completion_affidavit(mock_get_doc, mock_update_status):
    # Simulate a document with all required signatures for affidavit
    class DummyDoc:
        id = 1
        name = "TestDoc"
        doc_type = DocumentType.AFFIDAVIT
        status = DocumentStatus.PENDING
        uploaded_by = 1
        upload_date = "2024-01-01"
        blob_uri = "s3://bucket/key"
        document_hash = "abc123"
        signed_blob_uri = None
        signed_document_hash = None
        signatures = {
            "affiant": SignatureEntry(
                user_id=1, signature="abc123", timestamp=datetime.now()
            ),
            "notary": SignatureEntry(
                user_id=2, signature="def456", timestamp=datetime.now()
            ),
            "grantor": SignatureEntry(
                user_id=3, signature="ghi789", timestamp=datetime.now()
            ),
            "witness_1": SignatureEntry(
                user_id=4, signature="jkl000", timestamp=datetime.now()
            ),
            "witness_2": SignatureEntry(
                user_id=5, signature="mno999", timestamp=datetime.now()
            ),
        }

    mock_get_doc.return_value = DummyDoc()
    mock_update_status.return_value = AsyncMock()

    session = AsyncMock()
    result = await document_service.check_document_completion(1, session)

    assert result["is_complete"] is True
    assert result["missing_signatures"] == []
    # Verify that update_document_status was called since all signatures are present
    mock_update_status.assert_called_once_with(1, DocumentStatus.COMPLETED, session)


@pytest.mark.asyncio
@patch("app.services.document_service.get_document_by_id")
async def test_check_document_completion_deed_missing_grantee(mock_get_doc):
    # Simulate a document with all but grantee signed for a deed
    class DummyDoc:
        id = 2
        name = "TestDeed"
        doc_type = DocumentType.DEED
        status = DocumentStatus.PENDING
        uploaded_by = 1
        upload_date = "2024-01-01"
        blob_uri = "s3://bucket/key"
        document_hash = "abc123"
        signed_blob_uri = None
        signed_document_hash = None
        signatures = {
            "notary": SignatureEntry(
                user_id=1, signature="abc123", timestamp=datetime.now()
            ),
            "grantor": SignatureEntry(
                user_id=2, signature="def456", timestamp=datetime.now()
            ),
            "witness_1": SignatureEntry(
                user_id=3, signature="ghi789", timestamp=datetime.now()
            ),
            "witness_2": SignatureEntry(
                user_id=4, signature="jkl000", timestamp=datetime.now()
            ),
        }

    mock_get_doc.return_value = DummyDoc()
    session = AsyncMock()
    result = await document_service.check_document_completion(2, session)
    assert result["is_complete"] is False
    assert "grantee" in result["missing_signatures"]


@pytest.mark.asyncio
@patch("app.services.document_service.get_document_by_id")
async def test_update_document_status_success(mock_get_doc):
    # Test successful document status update
    from app.models.document import Document as DocumentModel

    # Create a mock document
    mock_doc = MagicMock(spec=DocumentModel)
    mock_doc.id = 1
    mock_doc.status = DocumentStatus.PENDING
    mock_get_doc.return_value = mock_doc

    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    # Mock the Document.model_validate to return a dict-like object
    with patch("app.services.document_service.Document") as MockDocument:
        MockDocument.model_validate.return_value = {
            "id": 1,
            "status": DocumentStatus.COMPLETED,
            "name": "test.pdf",
            "doc_type": DocumentType.AFFIDAVIT,
        }

        result = await document_service.update_document_status(
            1, DocumentStatus.COMPLETED, session
        )

        # Verify the document status was updated
        assert mock_doc.status == DocumentStatus.COMPLETED
        session.add.assert_called_once_with(mock_doc)
        session.commit.assert_called_once()
        session.refresh.assert_called_once_with(mock_doc)
        assert result["id"] == 1
        assert result["status"] == DocumentStatus.COMPLETED


@pytest.mark.asyncio
@patch("app.services.document_service.get_document_by_id")
async def test_update_document_status_document_not_found(mock_get_doc):
    # Test document not found scenario
    mock_get_doc.return_value = None

    session = AsyncMock()

    with pytest.raises(Exception) as exc_info:
        await document_service.update_document_status(
            999, DocumentStatus.COMPLETED, session
        )

    assert "Document not found" in str(exc_info.value)


@pytest.mark.asyncio
@patch("app.services.document_service.get_document_by_id")
async def test_update_document_status_database_error(mock_get_doc):
    # Test database error handling
    from app.models.document import Document as DocumentModel

    mock_doc = MagicMock(spec=DocumentModel)
    mock_doc.id = 1
    mock_doc.status = DocumentStatus.PENDING
    mock_get_doc.return_value = mock_doc

    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock(side_effect=Exception("Database error"))
    session.rollback = AsyncMock()

    with pytest.raises(Exception) as exc_info:
        await document_service.update_document_status(
            1, DocumentStatus.COMPLETED, session
        )

    assert "Failed to update document status" in str(exc_info.value)
    session.rollback.assert_called_once()
