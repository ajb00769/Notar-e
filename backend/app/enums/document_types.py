from enum import Enum


class DocumentType(str, Enum):
    AFFIDAVIT = "affidavit"
    DEED = "deed"
    CONTRACT = "contract"
    POWER_OF_ATTORNEY = "power_of_attorney"
