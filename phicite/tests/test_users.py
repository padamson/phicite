import pytest

from app.models.tortoise import User

#TODO: do this better; clean up users after tests
async def remove_user(username: str = None, email: str = None):
    existing_user = await User.filter(username="testuser").first()

    if existing_user:
        print(f"Deleting existing user: {existing_user.username}")
        await existing_user.delete()

    existing_user = await User.filter(email="cVwYH@example.com").first()

    if existing_user:
        print(f"Deleting existing user: {existing_user.email}")
        await existing_user.delete()

@pytest.mark.asyncio
async def test_create_user_valid_json(test_app_with_db):
    client, _, _ = test_app_with_db
    await remove_user(username="newuser", email="cVwYH@example.com")

    """Integration test for creating a user with valid JSON."""
    response = await client.post(
        "/users/",
        json={
            "username": "newuser",
            "email": "cVwYH@example.com",
            "full_name": "New User",
            "password": "dfASDFD2342#$#@#$@#@#"
        }
    )
    print(response.json())  # Debugging output
    assert response.status_code == 201
    response_dict = response.json()
    assert response_dict["username"] == "newuser"
    assert response_dict["email"] == "cVwYH@example.com"
    assert response_dict["full_name"] == "New User"
    assert "id" in response_dict
    assert "hashed_password" not in response_dict
    assert "password" not in response_dict

#TODO: parameterize this test with specific error messages for different invalid cases
@pytest.mark.asyncio
async def test_register_user_invalid_data(test_app_with_db):
    client, _, _ = test_app_with_db
    await remove_user(username="testuser", email="test@example.com")

    test_cases = [
        # Missing username
        {
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "dfASDFD2342#$#@#$@#@#"
        },
        # Invalid email
        {
            "username": "testuser",
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "dfASDFD2342#$#@#$@#@#"
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
        response = await client.post("/users/", json=invalid_data)
        assert response.status_code in (400, 422)

@pytest.mark.asyncio
async def test_authenticated_user_can_get_user_info(authenticated_client_with_db, setup_users):
    client, _ = authenticated_client_with_db
    user1, user2 = setup_users
    
    for endpoint, user in zip(["username", "email", "id"], [user1, user2]):
        val = user[endpoint]
        response = await client.get(f"/users/{endpoint}/{val}/")
        assert response.status_code == 200
        response_dict = response.json()
        assert response_dict["id"] == user["id"]
        assert response_dict["username"] == user["username"]
        assert response_dict["email"] == user["email"]
        assert response_dict["full_name"] == user["full_name"]

@pytest.mark.asyncio
async def test_unauthenticated_user_can_not_get_user_info(test_app_with_db, setup_users):
    client, _, _ = test_app_with_db
    user1, user2 = setup_users

    for endpoint, user in zip(["username", "email", "id"], [user1, user2]):
        val = user[endpoint]
        response = await client.get(f"/users/{endpoint}/{val}/")
        assert response.status_code == 401


#TODO: clean up this test
@pytest.mark.asyncio
async def test_authenticate_user(test_app_with_db):
    client, _, _ = test_app_with_db
    await remove_user(username="testuser", email="cVwYH@example.com")

    auth_payload = {
        "username": "testuser",
        "password": "dfASDFD2342#$#@#$@#@#"
    }

    # Create username and password form input
    response = await client.post(
        "/users/token",
        data={  # Use data parameter, not form_data
            "username": auth_payload["username"],
            "password": auth_payload["password"],
            "grant_type": "password",
            "scope": "",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

    new_user = {
        "username": "testuser",
        "email": "cVwYH@example.com",
        "full_name": "Test User",
        "password": "dfASDFD2342#$#@#$@#@#",
    }

    response = await client.post("/users/", json=new_user)
    assert response.status_code == 201
    response_dict = response.json()
    assert response_dict["username"] == new_user["username"]
    assert response_dict["email"] == new_user["email"]
    assert response_dict["full_name"] == new_user["full_name"]
    assert "id" in response_dict
    assert "hashed_password" not in response_dict
    assert "password" not in response_dict

    response = await client.post(
        "/users/token",
        data={
            "username": auth_payload["username"],
            "password": auth_payload["password"],
            "grant_type": "password",
            "scope": "",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    response_dict = response.json()
    assert response_dict["access_token"] is not None
    assert response_dict["token_type"] == "bearer"
    assert response_dict.keys() == {"access_token", "token_type"}

    auth_payload = {"username": "testuser", "password": "wrongpassword"}

    response = await client.post(
        "/users/token",
        data={
            "username": auth_payload["username"],
            "password": auth_payload["password"],
            "grant_type": "password",
            "scope": "",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}

@pytest.mark.asyncio
async def test_authenticated_user_can_get_me(authenticated_client_with_db):
    client, user, = authenticated_client_with_db 

    response = await client.get(
        "/users/me/"
    )
    assert response.status_code == 200
    response_dict = response.json()
    assert response_dict["username"] == user["username"]
    assert response_dict["email"] == user["email"]
    assert response_dict["full_name"] == user["full_name"]
    assert "id" in response_dict
    assert "hashed_password" not in response_dict
    assert "password" not in response_dict

@pytest.mark.asyncio
async def test_unauthenticated_user_can_not_get_me_or_my_highlights(test_app_with_db):
    client, _, _ = test_app_with_db

    response = await client.get(
        "/users/me/"
    )
    assert response.status_code == 401

    response = await client.get(
        "/users/me/highlights/"
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_authenticated_user_can_get_my_highlights(authenticated_client_with_db, test_highlights):
    client, user = authenticated_client_with_db
    # build list of highlights where username == user["username"]
    user_highlights = []
    for highlight_keys in test_highlights.keys():
        for highlight in test_highlights[highlight_keys]:
            if highlight["username"] == user["username"]:
                user_highlights.append(highlight)

    response = await client.get(
        "/users/me/highlights/"
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert isinstance(response.json()[0], dict)
    assert len(response.json()) == 4
    for highlight in response.json():
        assert highlight in user_highlights