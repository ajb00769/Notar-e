from fastapi import FastAPI
from app.api.routes import documents, appointments, auth
from app.core.db import init_db
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Notar-e API", version="1.0.0", lifespan=lifespan
)  # warning: ignore


app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
