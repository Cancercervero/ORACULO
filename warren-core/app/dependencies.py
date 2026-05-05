# warren-core/app/dependencies.py
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from typing import AsyncGenerator


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.session_factory() as session:
        yield session


def get_redis(request: Request) -> Redis:
    return request.app.state.redis
