from fastapi import APIRouter, Depends, status, Body, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.db import async_session
from app.models.notification import Notification
from typing import List
from datetime import datetime, timezone

router = APIRouter()


async def get_session():
    async with async_session() as session:
        yield session


@router.post("/", response_model=Notification, status_code=status.HTTP_201_CREATED)
async def create_notification(
    user_id: int = Body(...),
    message: str = Body(...),
    session: AsyncSession = Depends(get_session),
):
    try:
        notification = Notification(
            user_id=user_id,
            message=message,
            created_at=datetime.now(timezone.utc),
            read=False,
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        return notification
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}",
        )


@router.get("/", response_model=List[Notification])
async def get_notifications(
    user_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        result = await session.exec(
            Notification.select()
            .where(Notification.user_id == user_id, Notification.read == False)
            .order_by(Notification.created_at)
            .desc()
        )
        return result.all()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notifications: {str(e)}",
        )


@router.patch("/{notification_id}/read", response_model=Notification)
async def mark_notification_read(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        notification = await session.get(Notification, notification_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
            )
        notification.read = True
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        return notification
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}",
        )
