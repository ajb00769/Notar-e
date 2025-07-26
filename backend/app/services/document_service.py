from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models.document import Document as DocumentModel
from app.schemas.document import Document, DocumentCreate
from app.services.storage_service import generate_presigned_get_url
from app.core.hashing import generate_sha256_hash
from app.services.blockchain_service import notarize_document


async def create_document_entry(
    doc_data: DocumentCreate,
    s3_key: str,
    session: AsyncSession,
) -> Document:
    # Fetch the file for hashing via signed URL
    url = generate_presigned_get_url(s3_key)
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        file_bytes = response.content

    # Generate document hash
    doc_hash = generate_sha256_hash(file_bytes)
    blob_uri = f"s3://your-s3-bucket/{s3_key}"

    # Notarize on blockchain
    await notarize_document(
        document_hash=doc_hash,
        blob_uri=blob_uri,
        doc_type=doc_data.doc_type,
        user_id=doc_data.uploaded_by,
    )

    # Save to DB
    db_doc = DocumentModel(
        name=doc_data.name,
        date=doc_data.date,
        doc_type=doc_data.doc_type,
        uploaded_by=doc_data.uploaded_by,
        blob_uri=blob_uri,
        document_hash=doc_hash,
    )
    session.add(db_doc)
    await session.commit()
    await session.refresh(db_doc)

    return Document.from_attributes(db_doc)


async def list_documents(session: AsyncSession):
    docs = await session.exec(select(DocumentModel))
    return docs.all()


async def request_signatures():
    pass  # TODO: create functionality


async def get_documents():
    pass  # TODO: create functionality


async def create_document():
    pass  # TODO: create functionality


async def update_document_status(doc_id, status):
    pass  # TODO: create functionality
