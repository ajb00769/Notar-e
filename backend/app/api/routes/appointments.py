from fastapi import APIRouter, Depends, HTTPException, status
from app.core.db import async_session
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas.appointment import AppointmentCreate, AppointmentRead
from app.services.appointment_service import (
    create_appointment,
    list_appointments,
    get_appointment_by_id,
    update_appointment_status,
    cancel_appointment,
    complete_appointment,
    get_user_appointments,
)
from app.enums.appointment_status import AppointmentStatus
from app.core.auth import get_current_user
from app.schemas.user import User
from typing import List

router = APIRouter()


async def get_session():
    async with async_session() as session:
        yield session


@router.post("/", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def book(data: AppointmentCreate, session: AsyncSession = Depends(get_session)):
    return await create_appointment(data, session)


@router.get("/", response_model=List[AppointmentRead])
async def list_all(session: AsyncSession = Depends(get_session)):
    return await list_appointments(session)


@router.get("/{appointment_id}", response_model=AppointmentRead)
async def get_appointment(
    appointment_id: int, session: AsyncSession = Depends(get_session)
):
    appointment = await get_appointment_by_id(appointment_id, session)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
        )
    return AppointmentRead.model_validate(appointment)


@router.patch("/{appointment_id}/status", response_model=AppointmentRead)
async def update_status(
    appointment_id: int,
    new_status: AppointmentStatus,
    session: AsyncSession = Depends(get_session),
):
    return await update_appointment_status(appointment_id, new_status, session)


@router.patch("/{appointment_id}/cancel", response_model=AppointmentRead)
async def cancel(appointment_id: int, session: AsyncSession = Depends(get_session)):
    return await cancel_appointment(appointment_id, session)


@router.patch("/{appointment_id}/complete", response_model=AppointmentRead)
async def complete(appointment_id: int, session: AsyncSession = Depends(get_session)):
    return await complete_appointment(appointment_id, session)


@router.get("/user/{user_id}", response_model=List[AppointmentRead])
async def get_user_appointments_endpoint(
    user_id: int, session: AsyncSession = Depends(get_session)
):
    return await get_user_appointments(user_id, session)


@router.get("/my-appointments", response_model=List[AppointmentRead])
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await get_user_appointments(int(current_user.user_id), session)
