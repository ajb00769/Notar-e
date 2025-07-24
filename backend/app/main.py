from fastapi import FastAPI
from app.api.routes import documents, appointments
from app.core.db import init_db

app = FastAPI(title="Notar-e API", version="1.0.0")

@app.on_event("startup")
async def on_startup():
    await init_db()

app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(appointments.router, prefix="/appointments", tags=["Appointments"])
