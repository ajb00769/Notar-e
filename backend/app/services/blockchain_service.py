import httpx
from datetime import datetime, timezone
from app.enums.document_types import DocumentType

BLOCKCHAIN_API = "http://localhost:3000/notarize"  # Lisk Express backend


async def send_to_blockchain(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(BLOCKCHAIN_API, json=payload)
        response.raise_for_status()
        return response.json()


async def notarize_document(
    document_hash: str, blob_uri: str, doc_type: DocumentType, user_id: int
):
    payload = {
        "document_hash": document_hash,
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "notarized_by": user_id,
        "doc_type": doc_type.value,
        "blob_uri": blob_uri,
    }
    return await send_to_blockchain(payload)
