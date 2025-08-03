from enum import StrEnum


class SigningRole(StrEnum):
    NOTARY = "notary"
    AFFIANT = "affiant"  # Person making the sworn statement for affidavits
    WITNESS = "witness"
    GRANTOR = "grantor"  # Person creating/granting the document (contract creator)
    GRANTEE = "grantee"  # Person receiving rights/benefits from the document
    OTHER_SIGNER = "other_signer"  # For additional signers as needed
