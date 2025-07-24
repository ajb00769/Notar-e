import boto3
from botocore.client import Config
import os

BUCKET = "your-s3-bucket"
REGION = "us-east-1"
EXPIRE_SEC = 300

session = boto3.session.Session()
s3 = session.client("s3", region_name=REGION, config=Config(signature_version='s3v4'))

def upload_to_s3(file_bytes: bytes, key: str):
    s3.put_object(Bucket=BUCKET, Key=key, Body=file_bytes)

def generate_presigned_get_url(key: str):
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': BUCKET, 'Key': key},
        ExpiresIn=EXPIRE_SEC
    )
