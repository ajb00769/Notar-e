from app.models.document import DocumentType
from app.enums.signing_roles import SigningRole
from typing import Set


def get_required_signing_roles(doc_type: DocumentType) -> Set[str]:
    """
    Returns the set of required signing role strings for a given document type.
    - For affidavits: affiant, notary, 2 witnesses, grantor
    - For all other document types: notary, grantor, grantee, 2 witnesses
    """
    if doc_type == DocumentType.AFFIDAVIT:
        # affiant, notary, 2 witnesses, grantor
        return {
            SigningRole.AFFIANT.value,
            SigningRole.NOTARY.value,
            SigningRole.WITNESS.value + "_1",
            SigningRole.WITNESS.value + "_2",
            SigningRole.GRANTOR.value,
        }
    else:
        # notary, grantor, grantee, 2 witnesses
        return {
            SigningRole.NOTARY.value,
            SigningRole.GRANTOR.value,
            SigningRole.GRANTEE.value,
            SigningRole.WITNESS.value + "_1",
            SigningRole.WITNESS.value + "_2",
        }
