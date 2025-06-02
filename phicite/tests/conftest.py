import os
from datetime import datetime, UTC

import pytest
import pytest_asyncio
from starlette.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise


from app.main import create_application
from app.config import get_settings, Settings


def get_settings_override():
    return Settings(testing=1, database_url=os.environ.get("DATABASE_TEST_URL"))


@pytest.fixture(scope="module")
def test_app():
    app = create_application()
    app.dependency_overrides[get_settings] = get_settings_override
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture(scope="function")
async def test_app_with_db():
    app = create_application()
    app.dependency_overrides[get_settings] = get_settings_override
    
    await Tortoise.init(
        db_url=os.environ.get("DATABASE_TEST_URL"),
        modules={"models": ["app.models.tortoise"]},
    )
    await Tortoise.generate_schemas()
    
    async with AsyncClient(transport=ASGITransport(app=app), 
                           base_url=os.environ.get("BASE_URL")) as test_client:
        yield test_client
    
    await Tortoise.close_connections()


def current_datetime_utc_z():
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


