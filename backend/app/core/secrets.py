# for accessing secrets keeper/remote key store i.e. Azure Key Vault
from dotenv import load_dotenv
import os

load_dotenv()

S3_BUCKET = os.getenv("S3_BUCKET")
S3_REGION = os.getenv("S3_REGION")
