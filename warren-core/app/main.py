# warren-core/app/main.py
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import get_settings
from app.models.db import Base
from app.api.incidents import router as incidents_router
from app.api.websocket import router as ws_router, broadcast
from app.services import scenario_templates as tmpl
from app.services import redis_subscriber

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    tmpl.load_templates()

    subscriber_task = asyncio.create_task(
        redis_subscriber.run(app.state.redis, app.state.session_factory, broadcast)
    )

    logger.info("warren-core started — listening on :9000")
    yield

    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(title="warren-core", version="0.1.0", lifespan=lifespan)
app.include_router(incidents_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
