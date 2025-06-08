import os
from datetime import datetime, UTC, timedelta
import logging

import pytest
import pytest_asyncio
from starlette.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise
import jwt


from app.main import create_application
from app.config import get_settings, Settings
from app.models.tortoise import User, PDFHighlight
from app.models.pydantic import UserSchema
from app.auth import get_password_hash
from app.api import crud


@pytest.fixture
def mock_user():
    """Return a standard mock user for tests."""
    return UserSchema(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        disabled=False
    )

@pytest.fixture
def mock_auth(monkeypatch, mock_user):
    """Set up authentication mocking."""
    # Mock JWT decode
    def mock_jwt_decode(token, secret_key, algorithms):
        return {"sub": mock_user.username}
    
    # Mock user lookup
    async def mock_get_user_by_username(username):
        if username == mock_user.username:
            return mock_user
        return None
    
    # Apply mocks
    monkeypatch.setattr(jwt, "decode", mock_jwt_decode)
    monkeypatch.setattr(crud, "get_user_by_username", mock_get_user_by_username)
    
    return mock_user

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
    
    return {
        "access_token": token,
        "token_type": "bearer"
    }

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
        "password": "SecurePassword123!"
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
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        "password": "SecurePassword123!"
    }
    
    # Create second user
    user2 = {
        "username": "anotheruser",
        "email": "anotheruser@example.com",
        "full_name": "Another User",
        "password": "AnotherSecurePassword123!"
    }
    
    # Clean up any existing users first
    await User.filter(username=user1["username"]).delete()
    await User.filter(email=user1["email"]).delete()
    await User.filter(username=user2["username"]).delete()
    await User.filter(email=user2["email"]).delete()
    
    # Create users in database
    # You'll need to implement a function to create users directly
    user1_db = await create_user_directly(user1)
    user2_db = await create_user_directly(user2)
    
    assert user1_db.id != user2_db.id

    user1["id"] = user1_db.id
    user2["id"] = user2_db.id

    # Return both users
    yield user1, user2
    
    # Clean up after all tests
    await User.filter(username=user1["username"]).delete()
    await User.filter(email=user1["email"]).delete()
    await User.filter(username=user2["username"]).delete()
    await User.filter(email=user2["email"]).delete()


@pytest_asyncio.fixture(scope="function")
async def test_app_with_db(setup_users):
    app = create_application()
    user1, user2 = setup_users
    app.dependency_overrides[get_settings] = get_settings_override
    
    async with AsyncClient(transport=ASGITransport(app=app), 
                           base_url=os.environ.get("BASE_URL")) as test_client:
        yield test_client, user1, user2


@pytest_asyncio.fixture(scope="function")
async def authenticated_client_with_db(test_app_with_db):
    client, user1, _ = test_app_with_db
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
    client, _, user2 = test_app_with_db
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
async def test_highlights(setup_users):
    """
    Create all test highlights and clean up afterwards.
    Returns dictionaries for single_highlight, another_user_highlight, and multiple_highlights.
    """
    user1, user2 = setup_users
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
            user_id=user1["id"]
        )
        highlights_to_cleanup.append(single_highlight_obj)
        
        single_highlight = {
            "id": single_highlight_obj.id,
            "created_at": str(single_highlight_obj.created_at),
            "username": user1["username"],
            **base_highlight
        }
        
        # Create highlight for another user (user2)
        another_user_highlight_obj = await PDFHighlight.create(
            doi=base_highlight["doi"],
            highlight=base_highlight["highlight"],
            comment=base_highlight["comment"],
            user_id=user2["id"]
        )
        highlights_to_cleanup.append(another_user_highlight_obj)
        
        another_user_highlight = {
            "id": another_user_highlight_obj.id,
            "created_at": str(another_user_highlight_obj.created_at),
            "username": user2["username"],
            **base_highlight
        }
        
        # Create multiple highlights for user1
        multiple_highlights = []
        for i in range(3):
            multi_data = {
                "doi": f"10.1234/example.{5678+i}",
                "highlight": {
                    "1": {"rect": [100, 200, 300, 220], "text": f"highlight text {i}"}
                },
                "comment": f"Comment for highlight {i}"
            }
            
            multi_obj = await PDFHighlight.create(
                doi=multi_data["doi"],
                highlight=multi_data["highlight"],
                comment=multi_data["comment"],
                user_id=user1["id"]
            )
            highlights_to_cleanup.append(multi_obj)
            
            multiple_highlights.append({
                "id": multi_obj.id,
                "created_at": str(multi_obj.created_at),
                "username": user1["username"],
                **multi_data
            })
        
        # Yield all highlight data structures
        yield {
            "single_highlight": single_highlight,
            "another_user_highlight": another_user_highlight,
            "multiple_highlights": multiple_highlights
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


