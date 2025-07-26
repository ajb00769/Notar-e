from fastapi import APIRouter, Depends, HTTPException, status
from app.core.db import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas.appointment import AppointmentCreate, AppointmentRead
from app.services.appointment_service import create_appointment, list_appointments
from typing import List

router = APIRouter()


async def get_session():
    async with async_session() as session:
        yield session


@router.post("/", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def book(data: AppointmentCreate, session: AsyncSession = Depends(get_session)):
    try:
        return await create_appointment(data, session)
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {str(e)}",
        )


@router.get("/", response_model=List[AppointmentRead])
async def list_all(session: AsyncSession = Depends(get_session)):
    try:
        return await list_appointments(session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve appointments: {str(e)}",
        )
