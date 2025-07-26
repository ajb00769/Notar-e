from typing import Optional
from sqlmodel import SQLModel, Field
from app.enums.user_roles import UserRole


class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    last_name: str
    first_name: str
    middle_name: Optional[str]
    hashed_password: str
    role: UserRole = UserRole.USER
