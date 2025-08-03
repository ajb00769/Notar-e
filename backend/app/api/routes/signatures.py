from fastapi import APIRouter

router = APIRouter()


# TODO: Signature private key creation endpoint, should be used only once per account.
#  Signature private keys are permanent per account.
@router.post("/create")
def create_signature():
    # Signature private keys should be based on Physical ID numbers based on the
    # government ID the user uploaded. Hashing algorithms used should be random as
    # well for each user
    pass
