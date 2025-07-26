from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin" # site administrator
    SUPER_ADMIN = "super_admin"
    NOTARY = "notary"
    USER = "user" # ordinary user