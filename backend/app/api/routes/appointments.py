from fastapi import APIRouter, Depends
from app.core.db import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas.appointment import AppointmentCreate, AppointmentRead
from app.services.appointment_service import create_appointment, list_appointments

router = APIRouter()


async def get_session():
    async with async_session() as session:
        yield session


@router.post("/", response_model=AppointmentRead)
async def book(data: AppointmentCreate, session: AsyncSession = Depends(get_session)):
    return await create_appointment(data, session)


@router.get("/", response_model=list[AppointmentRead])
async def list_all(session: AsyncSession = Depends(get_session)):
    return await list_appointments(session)
