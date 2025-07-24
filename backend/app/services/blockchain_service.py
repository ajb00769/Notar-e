import httpx
from datetime import datetime

BLOCKCHAIN_API = "http://localhost:3000/notarize"  # Lisk Express backend

async def send_to_blockchain(payload: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(BLOCKCHAIN_API, json=payload)
        response.raise_for_status()
        return response.json()

async def notarize_document(document_hash: str, blob_uri: str, doc_type: str, user_id: str):
    payload = {
        "document_hash": document_hash,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "notarized_by": user_id,
        "doc_type": doc_type,
        "blob_uri": blob_uri
        # You can later add a digital signature field here
    }
    return await send_to_blockchain(payload)