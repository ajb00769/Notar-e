import hashlib

def generate_sha256_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
