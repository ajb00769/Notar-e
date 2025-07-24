from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.appointment import Appointment

async def create_appointment(data, session: AsyncSession):
    appt = Appointment(**data.dict())
    session.add(appt)
    await session.commit()
    await session.refresh(appt)
    return appt

async def list_appointments(session: AsyncSession):
    result = await session.exec(select(Appointment))
    return result.all()
