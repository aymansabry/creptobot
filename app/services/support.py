# app/services/support.py
from app.database.models import SupportTicket
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

class SupportService:

    @staticmethod
    async def create_ticket(session: AsyncSession, user_id: int, message: str):
        ticket = SupportTicket(
            user_id=user_id,
            message=message,
            created_at=datetime.utcnow(),
            status="open"
        )
        session.add(ticket)
        await session.commit()
        return ticket

    @staticmethod
    async def get_user_tickets(session: AsyncSession, user_id: int):
        result = await session.execute(select(SupportTicket).where(SupportTicket.user_id == user_id))
        return result.scalars().all()

    @staticmethod
    async def close_ticket(session: AsyncSession, ticket_id: int):
        result = await session.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if ticket:
            ticket.status = "closed"
            await session.commit()
            return True
        return False

    @staticmethod
    async def get_all_open_tickets(session: AsyncSession):
        result = await session.execute(select(SupportTicket).where(SupportTicket.status == "open"))
        return result.scalars().all()
