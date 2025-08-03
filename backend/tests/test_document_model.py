from app.models.document import Document, DocumentStatus, DocumentType
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
