import pytest
import pytest_asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models.db import Base


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            yield session
    finally:
        await engine.dispose()


@pytest.fixture
def load_templates():
    from app.services import scenario_templates as tmpl
    path = Path(__file__).parent.parent / "data" / "scenario_templates.json"
    if path.exists():
        tmpl.load_templates(path)
