import boto3
from botocore.client import Config
from app.core.secrets import S3_BUCKET, S3_REGION

EXPIRE_SEC = 300

session = boto3.session.Session()
s3 = session.client(
    "s3", region_name=S3_REGION, config=Config(signature_version="s3v4")
)


def upload_to_s3(file_bytes: bytes, key: str):
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=file_bytes)


def delete_from_s3(key: str):
    s3.delete_object(Bucket=S3_BUCKET, Key=key)


def generate_presigned_get_url(key: str):
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=EXPIRE_SEC,
    )
