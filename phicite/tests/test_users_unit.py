import pytest
from app import auth
from app.api import crud
from app.models.pydantic import UserCreate, UserSchema, UserInDBSchema
from app.api.users import authenticate_user

def test_register_user(test_app, monkeypatch):
    """Test user registration endpoint"""
    # Test user data
    new_user_create = UserCreate(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        password="SDFDS23423SDdfsasdf$#$@$"
    )
    
    # Mock response for user creation
    new_user_response = UserSchema(
        id=1,
        username=new_user_create.username,
        email=new_user_create.email,
        full_name=new_user_create.full_name,
        disabled=False
    )
    
    # Mock the password hashing function
    async def mock_get_password_hash(password):
        return "hashed_password"
    
    # Mock the database create_user function
    async def mock_post_user_db(new_user_data):
        return new_user_response
    
    # Apply the mocks
    monkeypatch.setattr(auth, "get_password_hash", mock_get_password_hash)
    monkeypatch.setattr(crud, "post_user", mock_post_user_db)
    
    # Make the request
    response = test_app.post("/users/", json=new_user_create.model_dump())
    
    # Verify response
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["username"] == new_user_response.username
    assert user_data["email"] == new_user_response.email
    assert user_data["full_name"] == new_user_response.full_name
    assert user_data["id"] == new_user_response.id
    assert new_user_create.password not in str(user_data)
    assert "hashed_password" not in str(user_data)


def test_register_user_duplicate_username(test_app, monkeypatch):
    """Test registration with duplicate username"""
    # Test user data
    new_user = {
        "username": "existinguser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "SDFDS23423SDdfsasdf$#$@$"
    }
    
    # Create a mock user that would be returned by the filter
    mock_existing_user = type('UserSchema', (), {
        "username": new_user["username"],
        "email": "different@example.com",  # Different email
        "id": 123
    })
    
    # Mock User.filter to return our mock user when filtering by username
    def mock_filter(*args, **kwargs):
        # Check if we're filtering by username
        if kwargs.get('username') == new_user["username"]:
            # Return a mock QuerySet that will return our mock user
            class MockQuerySet:
                async def first(self):
                    return mock_existing_user
            return MockQuerySet()
        # For any other filter, return empty result
        class EmptyQuerySet:
            async def first(self):
                return None
        return EmptyQuerySet()
    
    # Apply the mock
    monkeypatch.setattr("app.models.tortoise.User.filter", mock_filter)
    
    # Make the request
    response = test_app.post("/users/", json=new_user)
    
    # Verify response
    assert response.status_code == 400
    assert "Username 'existinguser' already exists" in response.json()["detail"]


#TODO: parameterize this test with specific error messages for different invalid cases
def test_register_user_invalid_data(test_app):
    """Test registration with invalid data"""
    # Test cases with invalid data
    test_cases = [
        # Missing username
        {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "DFSsdfd$#@3432dfdalkj"
        },
        # Invalid email
        {
            "username": "testuser",
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "DFSsdfd$#@3432dfdalkj"
        },
        # Password too short (if you have validation)
        {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "short"
        }
    ]
    
    for invalid_data in test_cases:
        response = test_app.post("/users/", json=invalid_data)
        assert response.status_code in (400, 422)  # Validation error codes

def test_register_user_duplicate_email(test_app, monkeypatch):
    """Test registration with duplicate email"""
    # Test user data
    new_user = {
        "username": "newusername",
        "email": "existingemail@example.com",
        "full_name": "Test User",
        "password": "DFSsdfd$#@3432dfdalkj"
    }
    
    # Create a mock user that would be returned by the filter
    mock_existing_user = type('UserSchema', (), {
        "username": "different_username",  # Different username
        "email": new_user["email"], # Existing email
        "id": 123
    })
    
    # Mock User.filter to return our mock user when filtering by email
    def mock_filter(*args, **kwargs):
        # Check if we're filtering by email
        if kwargs.get('email') == new_user["email"]:
            # Return a mock QuerySet that will return our mock user
            class MockQuerySet:
                async def first(self):
                    return mock_existing_user
            return MockQuerySet()
        # For any other filter, return empty result
        class EmptyQuerySet:
            async def first(self):
                return None
        return EmptyQuerySet()
    
    # Apply the mock
    monkeypatch.setattr("app.models.tortoise.User.filter", mock_filter)
    
    # Make the request
    response = test_app.post("/users/", json=new_user)
    
    # Verify response
    assert response.status_code == 400
    assert "Email 'existingemail@example.com' already exists" in response.json()["detail"]

def test_get_user_by_username(test_app, monkeypatch, mock_auth, auth_headers):
    
    # Mock User.filter to return our mock user when filtering by username
    def mock_filter(*args, **kwargs):
        if kwargs.get('username') == mock_auth.username:
            class MockQuerySet:
                async def first(self):
                    return mock_auth
            return MockQuerySet()
        class EmptyQuerySet:
            async def first(self):
                return None
        return EmptyQuerySet()
    # Apply the mock
    monkeypatch.setattr("app.models.tortoise.User.filter", mock_filter)
    # Make the request
    response = test_app.get(
        f"/users/username/{mock_auth.username}/", headers=auth_headers
    )
    # Verify response
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == mock_auth.username
    assert user_data["email"] == mock_auth.email
    assert user_data["full_name"] == mock_auth.full_name

def test_get_user_by_email(test_app, monkeypatch, mock_auth, auth_headers):
    def mock_filter(*args, **kwargs):
        if kwargs.get('email') == mock_auth.email:
            class MockQuerySet:
                async def first(self):
                    return mock_auth
            return MockQuerySet()
        class EmptyQuerySet:
            async def first(self):
                return None
        return EmptyQuerySet()
    # Apply the mock
    monkeypatch.setattr("app.models.tortoise.User.filter", mock_filter)
    # Make the request
    response = test_app.get(f"/users/email/{mock_auth.email}/", headers=auth_headers)
    # Verify response
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == mock_auth.username
    assert user_data["email"] == mock_auth.email
    assert user_data["full_name"] == mock_auth.full_name

def test_get_user_by_id(test_app, monkeypatch, mock_auth, auth_headers):
    def mock_filter(*args, **kwargs):
        if kwargs.get('id') == mock_auth.id:
            class MockQuerySet:
                async def first(self):
                    return mock_auth
            return MockQuerySet()
        class EmptyQuerySet:
            async def first(self):
                return None
        return EmptyQuerySet()
    # Apply the mock
    monkeypatch.setattr("app.models.tortoise.User.filter", mock_filter)
    # Make the request
    response = test_app.get(f"/users/id/{mock_auth.id}/", headers=auth_headers)
    # Verify response
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == mock_auth.username
    assert user_data["email"] == mock_auth.email
    assert user_data["full_name"] == mock_auth.full_name

@pytest.mark.asyncio
async def test_authenticate_user(monkeypatch):
    username_from_form="testuser"
    password_from_form="dfASDFD2342#$#@#$@#@#"

    mock_user = UserInDBSchema(
        id=1,
        username=username_from_form,
        email="cVwYH@example.com",
        full_name="Test User",
        disabled=False, 
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    )

    def mock_verify_password(plain_password, hashed_password):
        return True
    
    monkeypatch.setattr(auth, "verify_password", mock_verify_password)
    
    async def mock_get_user_in_db_by_username(username):
        if username == username_from_form:
            return mock_user
        return None
    
    monkeypatch.setattr(crud, "get_user_in_db_by_username", mock_get_user_in_db_by_username)

    authenticated_user = await authenticate_user(username_from_form, password_from_form)

    assert authenticated_user.username == username_from_form
    assert authenticated_user.id == mock_user.id
    assert authenticated_user.disabled == mock_user.disabled
    assert authenticated_user.email == mock_user.email