import os
from datetime import datetime, UTC, timedelta
import logging

import unittest.mock
import pytest
import pytest_asyncio
from starlette.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise
import jwt


from app.main import create_application
from app.config import get_settings, Settings
from app.models.tortoise import User, PDFHighlight
from app.models.pydantic import UserSchema, TokenDataSchema, AuthSchema
from app.auth import get_password_hash
from app.api import crud
from app.api import users


@pytest.fixture(scope="function")
def mock_admin_user():
    return UserSchema(
        id=1,
        username="adminuser",
        email="admin@example.com",
        full_name="Admin User",
        disabled=False,
        is_admin=True
    )

@pytest.fixture(scope="function")
def mock_user():
    return UserSchema(
        id=2,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        disabled=False,
        is_admin=False
    )

@pytest_asyncio.fixture(scope="function")
async def mock_get_user_by_username(monkeypatch, mock_user, mock_admin_user):
    # Create a standalone side effect function
    async def custom_side_effect(username: str):
        if username == mock_admin_user.username:
            return mock_admin_user
        elif username == mock_user.username:
            return mock_user
        return None

    # Create the mock and configure it
    async_mock = unittest.mock.AsyncMock()
    async_mock.configure_mock(side_effect=custom_side_effect)
    
    # Apply the mock to crud
    monkeypatch.setattr(crud, "get_user_by_username", async_mock)
    
    return async_mock

@pytest_asyncio.fixture(scope="function")
async def mock_get_user_by_email(monkeypatch, mock_user, mock_admin_user):
    # Create a standalone side effect function
    async def custom_side_effect(email: str):
        if email == mock_admin_user.email:
            return mock_admin_user
        elif email == mock_user.email:
            return mock_user
        return None

    # Create the mock and configure it
    async_mock = unittest.mock.AsyncMock()
    async_mock.configure_mock(side_effect=custom_side_effect)
    
    # Apply the mock to crud
    monkeypatch.setattr(crud, "get_user_by_email", async_mock)
    
    return async_mock

@pytest_asyncio.fixture(scope="function")
async def mock_get_user_by_id(monkeypatch, mock_user, mock_admin_user):
    # Create a standalone side effect function
    async def custom_side_effect(id: int):
        if id == mock_admin_user.id:
            return mock_admin_user
        elif id == mock_user.id:
            return mock_user
        return None

    # Create the mock and configure it
    async_mock = unittest.mock.AsyncMock()
    async_mock.configure_mock(side_effect=custom_side_effect)
    
    # Apply the mock to crud
    monkeypatch.setattr(crud, "get_user_by_id", async_mock)
    
    return async_mock


@pytest.fixture(scope="function")
def mock_jwt_decode_admin_user(monkeypatch, mock_admin_user):
    def mock_jwt_decode(token, secret_key, algorithms):
        return {"sub": mock_admin_user.username}

    monkeypatch.setattr(jwt, "decode", mock_jwt_decode)
    return TokenDataSchema(username=mock_admin_user.username)


@pytest.fixture(scope="function")
def mock_jwt_decode_user(monkeypatch, mock_user):
    def mock_jwt_decode(token, secret_key, algorithms):
        return {"sub": mock_user.username}

    monkeypatch.setattr(jwt, "decode", mock_jwt_decode)
    return TokenDataSchema(username=mock_user.username)


@pytest_asyncio.fixture(scope="function")
async def mock_get_user_by_token_data_admin(monkeypatch, mock_admin_user):
    async def custom_side_effect(token_data: TokenDataSchema):
        return mock_admin_user

    async_mock = unittest.mock.AsyncMock()
    async_mock.configure_mock(side_effect=custom_side_effect)
    monkeypatch.setattr(crud, "get_user_by_token_data", async_mock)
    
    return async_mock

@pytest_asyncio.fixture(scope="function")
async def mock_get_user_by_token_data_user(monkeypatch, mock_user):
    async def custom_side_effect(token_data: TokenDataSchema):
        return mock_user

    async_mock = unittest.mock.AsyncMock()
    async_mock.configure_mock(side_effect=custom_side_effect)
    monkeypatch.setattr(crud, "get_user_by_token_data", async_mock)
    
    return async_mock


@pytest.fixture(scope="function")
def mock_get_authorized_admin_user(monkeypatch, mock_admin_user):
    # Create a mock for the inner dependency function
    async def mock_dependency(*args, **kwargs):
        return AuthSchema(**mock_admin_user.model_dump(), authorized=True)
    
    dependency_mock = unittest.mock.AsyncMock(side_effect=mock_dependency)
    
    # Create a mock for get_authorized_active_user that returns our dependency mock
    def mock_get_authorized_active_user(*args, **kwargs):
        return dependency_mock
    
    # Apply the mock
    monkeypatch.setattr(users, "get_authorized_active_user", mock_get_authorized_active_user)
    
    # Return the dependency mock for assertions
    return dependency_mock


@pytest.fixture
def auth_headers():
    """Return headers with a fake authentication token."""
    return {"Authorization": "Bearer fake_valid_token"}


async def create_test_token(username="fakeuser"):
    # Match the same parameters used in your app's token creation
    expiration = datetime.now(UTC) + timedelta(minutes=30)

    payload = {
        "sub": username,  # Subject (typically username)
        "exp": expiration.timestamp(),  # Expiration time
        "iat": datetime.now(UTC).timestamp(),  # Issued at time
        # Add any other claims your application uses
    }

    # Use the same secret key and algorithm as your application
    secret_key = os.environ.get("JWT_SECRET_KEY")
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")

    # Create the token
    token = jwt.encode(payload, secret_key, algorithm=algorithm)

    return {"access_token": token, "token_type": "bearer"}


def get_settings_override():
    return Settings(testing=1, database_url=os.environ.get("DATABASE_TEST_URL"))


@pytest.fixture(scope="function")
def test_app():
    app = create_application()
    app.dependency_overrides[get_settings] = get_settings_override
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(test_app):
    fake_user = {
        "id": 1,
        "username": "fakeuser",
        "email": "fake@example.com",
        "full_name": "Fake User",
        "password": "SecurePassword123!",
    }

    # fake token
    token = await create_test_token(username=fake_user["username"])

    # Create a client with authentication headers
    client = test_app
    client.headers.update({"Authorization": f"Bearer {token['access_token']}"})

    yield client, fake_user


@pytest_asyncio.fixture(scope="function")
async def init_test_db():
    logger = logging.getLogger("test_db")
    logger.setLevel(logging.DEBUG)

    # Create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    db_url = os.environ.get("DATABASE_TEST_URL")
    logger.info(f"Connecting to database with URL: {db_url}")

    try:
        logger.info("Initializing Tortoise...")
        await Tortoise.init(
            db_url=os.environ.get("DATABASE_TEST_URL"),
            modules={"models": ["app.models.tortoise"]},
        )

        # Get connection
        _ = Tortoise.get_connection("default")

        # Get all model classes
        models = Tortoise.apps.get("models").values()

        # Clear all tables (more selective than dropping the whole database)
        for model in models:
            if hasattr(model, "_meta") and hasattr(model._meta, "table"):
                logger.info(f"Clearing table: {model._meta.table}")
                await model.all().delete()

        # Generate schemas to ensure all tables exist with correct structure
        await Tortoise.generate_schemas()

        yield
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        logger.exception("Full exception details:")
        raise
    finally:
        logger.info("Cleaning up database connections...")
        try:
            await Tortoise.close_connections()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing connections: {str(e)}")
            logger.exception("Full exception details:")


async def create_user_directly(user_data):
    user = User(
        username=user_data["username"],
        email=user_data["email"],
        full_name=user_data["full_name"],
        hashed_password=get_password_hash(user_data["password"]),
        is_admin=user_data.get("is_admin", False),
    )
    await user.save()
    return user


@pytest_asyncio.fixture(scope="function")
async def setup_users(init_test_db):
    """Create test users once for all tests"""
    # Create first user
    user1 = {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "SecurePassword123!",
    }

    # Create second user
    user2 = {
        "username": "anotheruser",
        "email": "anotheruser@example.com",
        "full_name": "Another User",
        "password": "AnotherSecurePassword123!",
    }

    admin = {
        "username": "adminuser",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password": "AdminSecurePassword123!",
        "is_admin": True,
    }

    # Clean up any existing users first
    await User.filter(username=user1["username"]).delete()
    await User.filter(email=user1["email"]).delete()
    await User.filter(username=user2["username"]).delete()
    await User.filter(email=user2["email"]).delete()
    await User.filter(username=admin["username"]).delete()
    await User.filter(email=admin["email"]).delete()

    # Create users in database
    # You'll need to implement a function to create users directly
    user1_db = await create_user_directly(user1)
    user2_db = await create_user_directly(user2)
    admin_db = await create_user_directly(admin)

    assert user1_db.id != user2_db.id != admin_db.id

    user1["id"] = user1_db.id
    user2["id"] = user2_db.id
    admin["id"] = admin_db.id

    assert admin_db.is_admin

    # Return both users
    yield user1, user2, admin

    # Clean up after all tests
    await User.filter(username=user1["username"]).delete()
    await User.filter(email=user1["email"]).delete()
    await User.filter(username=user2["username"]).delete()
    await User.filter(email=user2["email"]).delete()
    await User.filter(username=admin["username"]).delete()
    await User.filter(email=admin["email"]).delete()


@pytest_asyncio.fixture(scope="function")
async def test_app_with_db(setup_users):
    app = create_application()
    user1, user2, admin = setup_users
    app.dependency_overrides[get_settings] = get_settings_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=os.environ.get("BASE_URL")
    ) as test_client:
        yield test_client, user1, user2, admin


@pytest_asyncio.fixture(scope="function")
async def authenticated_client_with_db(test_app_with_db):
    client, user1, _, _ = test_app_with_db
    client.headers.pop("Authorization", None)

    # Authenticate with the first user
    response = await client.post(
        "/users/token",
        data={
            "username": user1["username"],
            "password": user1["password"],
            "grant_type": "password",
            "scope": "",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a client with authentication headers
    client.headers.update({"Authorization": f"Bearer {token}"})

    yield client, user1


@pytest_asyncio.fixture(scope="function")
async def another_authenticated_client_with_db(test_app_with_db):
    client, _, user2, _ = test_app_with_db
    client.headers.pop("Authorization", None)

    # Authenticate with the second user
    response = await client.post(
        "/users/token",
        data={
            "username": user2["username"],
            "password": user2["password"],
            "grant_type": "password",
            "scope": "",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a client with authentication headers
    client.headers.update({"Authorization": f"Bearer {token}"})

    yield client, user2

@pytest_asyncio.fixture(scope="function")
async def authenticated_admin_client_with_db(test_app_with_db):
    client, _, _, admin = test_app_with_db
    client.headers.pop("Authorization", None)

    # Authenticate with the admin user
    response = await client.post(
        "/users/token",
        data={
            "username": admin["username"],
            "password": admin["password"],
            "grant_type": "password",
            "scope": "",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a client with authentication headers
    client.headers.update({"Authorization": f"Bearer {token}"})

    # Check if the user is an admin
    response = await client.get("/users/me/")
    assert response.status_code == 200
    response_dict = response.json()
    assert response_dict["username"] == admin["username"]
    assert response_dict["is_admin"]
    assert response_dict["id"] == admin["id"]

    yield client, admin


@pytest_asyncio.fixture(scope="function")
async def test_highlights(setup_users):
    """
    Create all test highlights and clean up afterwards.
    Returns dictionaries for single_highlight, another_user_highlight, and multiple_highlights.
    """
    user1, user2, _ = setup_users
    highlights_to_cleanup = []

    # Base highlight data template
    base_highlight = {
        "doi": "10.1234/example.5678",
        "highlight": {
            "1": {"rect": [100, 200, 300, 220], "text": "first part"},
            "2": {"rect": [50, 100, 250, 120], "text": "second part"},
        },
        "comment": "This is an important passage",
    }

    try:
        # Create single highlight for user1
        single_highlight_obj = await PDFHighlight.create(
            doi=base_highlight["doi"],
            highlight=base_highlight["highlight"],
            comment=base_highlight["comment"],
            user_id=user1["id"],
        )
        highlights_to_cleanup.append(single_highlight_obj)

        single_highlight = {
            "id": single_highlight_obj.id,
            "created_at": str(single_highlight_obj.created_at),
            "username": user1["username"],
            **base_highlight,
        }

        # Create highlight for another user (user2)
        another_user_highlight_obj = await PDFHighlight.create(
            doi=base_highlight["doi"],
            highlight=base_highlight["highlight"],
            comment=base_highlight["comment"],
            user_id=user2["id"],
        )
        highlights_to_cleanup.append(another_user_highlight_obj)

        another_user_highlight = {
            "id": another_user_highlight_obj.id,
            "created_at": str(another_user_highlight_obj.created_at),
            "username": user2["username"],
            **base_highlight,
        }

        # Create multiple highlights for user1
        multiple_highlights = []
        for i in range(3):
            multi_data = {
                "doi": f"10.1234/example.{5678 + i}",
                "highlight": {
                    "1": {"rect": [100, 200, 300, 220], "text": f"highlight text {i}"}
                },
                "comment": f"Comment for highlight {i}",
            }

            multi_obj = await PDFHighlight.create(
                doi=multi_data["doi"],
                highlight=multi_data["highlight"],
                comment=multi_data["comment"],
                user_id=user1["id"],
            )
            highlights_to_cleanup.append(multi_obj)

            multiple_highlights.append(
                {
                    "id": multi_obj.id,
                    "created_at": str(multi_obj.created_at),
                    "username": user1["username"],
                    **multi_data,
                }
            )

        # Yield all highlight data structures
        yield {
            "single_highlight": [single_highlight],
            "another_user_highlight": [another_user_highlight],
            "multiple_highlights": multiple_highlights,
        }

    finally:
        # Clean up all created highlights
        for highlight in highlights_to_cleanup:
            try:
                await highlight.delete()
            except Exception as e:
                print(f"Error deleting highlight {highlight.id}: {e}")


def current_datetime_utc_z():
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
