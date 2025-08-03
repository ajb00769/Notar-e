from fastapi import FastAPI
from app.api.routes import documents, appointments, auth, signatures
from app.core.db import init_db
from contextlib import asynccontextmanager
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Notar-e API", version="1.0.0", lifespan=lifespan
)  # warning: ignore


app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(
    appointments.router, prefix="/api/appointments", tags=["Appointments"]
)
app.include_router(signatures.router, prefix="/api/signatures", tags=["Signatures"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
