from pydantic import BaseModel
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
