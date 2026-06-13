from sqlalchemy.ext.asyncio import AsyncSession
from qdra.infrastructure.db.models import Base


async def init_db(session: AsyncSession):
    async with session.begin():
        await session.run_sync(Base.metadata.create_all)
