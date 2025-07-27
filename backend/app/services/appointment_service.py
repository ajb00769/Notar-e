from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.appointment import Appointment
from app.schemas.appointment import AppointmentCreate, AppointmentRead
from app.enums.appointment_status import AppointmentStatus
from app.enums.user_roles import UserRole
from fastapi import HTTPException, status
from typing import List, Optional


async def create_appointment(
    data: AppointmentCreate, session: AsyncSession
) -> AppointmentRead:
    """Create a new appointment."""
    try:
        appt = Appointment(**data.model_dump())
        session.add(appt)
        await session.commit()
        await session.refresh(appt)
        return AppointmentRead.model_validate(appt)
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appointment: {str(e)}",
        )


async def list_appointments(session: AsyncSession) -> List[AppointmentRead]:
    """List all appointments."""
    try:
        result = await session.exec(select(Appointment))
        return [AppointmentRead.model_validate(appt) for appt in result.all()]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve appointments: {str(e)}",
        )


async def get_appointment_by_id(
    appointment_id: int, session: AsyncSession
) -> Optional[Appointment]:
    """Get an appointment by ID."""
    try:
        appointment = await session.get(Appointment, appointment_id)
        return appointment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve appointment: {str(e)}",
        )


async def update_appointment_status(
    appointment_id: int,
    new_status: AppointmentStatus,
    user_id: int,
    user_role: UserRole,
    session: AsyncSession,
) -> AppointmentRead:
    """Update appointment status (restricted to owner or privileged roles)."""
    try:
        appointment = await get_appointment_by_id(appointment_id, session)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found"
            )
        # Restrict to owner or privileged roles
        if not (
            appointment.user_id == user_id
            or user_role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this appointment.",
            )
        appointment.status = new_status
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        return AppointmentRead.model_validate(appointment)
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update appointment status: {str(e)}",
        )


async def cancel_appointment(
    appointment_id: int, user_id: int, user_role: UserRole, session: AsyncSession
) -> AppointmentRead:
    """Cancel an appointment (restricted to owner or privileged roles)."""
    return await update_appointment_status(
        appointment_id, AppointmentStatus.CANCELLED, user_id, user_role, session
    )


async def complete_appointment(
    appointment_id: int, user_id: int, user_role: UserRole, session: AsyncSession
) -> AppointmentRead:
    """Mark an appointment as completed (restricted to owner or privileged roles)."""
    return await update_appointment_status(
        appointment_id, AppointmentStatus.COMPLETED, user_id, user_role, session
    )


async def get_user_appointments(
    user_id: int, session: AsyncSession
) -> List[AppointmentRead]:
    """Get all appointments for a specific user."""
    try:
        result = await session.exec(
            select(Appointment).where(Appointment.user_id == user_id)
        )
        return [AppointmentRead.model_validate(appt) for appt in result.all()]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user appointments: {str(e)}",
        )
