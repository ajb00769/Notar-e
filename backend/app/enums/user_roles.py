from enum import IntEnum


class UserRole(IntEnum):
    SUPER_ADMIN = 0
    ADMIN = 1
    NOTARY = 2
    USER = 3
