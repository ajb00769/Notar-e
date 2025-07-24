from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    date: date
    doc_type: str
    status: str
    uploaded_by: str
    blob_uri: str
    document_hash: str
    signatures: Optional[dict] = Field(default_factory=dict, sa_column=Field(sa_column=JSON))