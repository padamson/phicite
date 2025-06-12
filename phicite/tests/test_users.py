import pytest

from app.models.tortoise import User



@pytest.mark.asyncio
async def test_register_user_valid_json(test_app_with_db):
    client, _, _, _ = test_app_with_db

    user_dict = {
        "username": "testuser2",
        "email": "test2@example.com",
        "full_name": "Test User2",
        "password": "dfASDFD2342#$#@#$@#@#"
    }

    response = await client.post(
        "/users/",
        json=user_dict
    )
    print(response.json())  # Debugging output
    assert response.status_code == 201
    response_dict = response.json()
    assert response_dict["username"] == user_dict["username"]
    assert response_dict["email"] == user_dict["email"]
    assert response_dict["full_name"] == user_dict["full_name"]
    assert "id" in response_dict
    assert "hashed_password" not in response_dict
    assert "password" not in response_dict

    # Use tortoise ORM to clean up after test
    user = await User.get(id=response_dict["id"])
    await user.delete()


#TODO: parameterize this test with specific error messages for different invalid cases
@pytest.mark.asyncio
async def test_register_user_invalid_data(test_app_with_db):
    client, _, _, _ = test_app_with_db

    before_users = await User.all()

    test_cases = [
        # Missing username
        {
            "email": "test2@example.com",
            "full_name": "Test User",
            "password": "dfASDFD2342#$#@#$@#@#"
        },
        # Invalid email
        {
            "username": "testuser2",
            "email": "not-an-email",
            "full_name": "Test User",
            "password": "dfASDFD2342#$#@#$@#@#"
        },
        # Missing password
        {
            "username": "testuser2",
            "email": "test2@example.com",
            "full_name": "Test User"
        },
        # Missing email
        {
            "username": "testuser2",
            "full_name": "Test User",
            "password": "dfASDFD2342#$#@#$@#@#"
        },
        # Password too short (if you have validation)
        {
            "username": "testuser2",
            "email": "test2@example.com",
            "full_name": "Test User",
            "password": "short"
        },
        # Duplicate username
        {
            "username": "testuser",
            "email": "test2@example.com",
            "full_name": "Test User",
            "password": "dfASDFD2342#$#@#$@#@#"
        },
        # Duplicate email
        {
            "username": "testuser2",
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "dfASDFD2342#$#@#$@#@#"
        }
    ]
    
    for invalid_data in test_cases:
        response = await client.post("/users/", json=invalid_data)
        assert response.status_code in (400, 422)

    after_users = await User.all()
    assert before_users == after_users


@pytest.mark.asyncio
async def test_admin_user_can_delete_user(authenticated_admin_client_with_db, setup_users):
    client, _ = authenticated_admin_client_with_db
    user1, user2, admin = setup_users

    for user in [user1, user2]:
        response = await client.delete(f"/users/admin/username/{user['username']}/")
        assert response.status_code == 200

    # Check that the user was deleted using tortoise ORM
    for user in [user1, user2]:
        user_in_db = await User.filter(username=user["username"]).first()
        assert not user_in_db

@pytest.mark.asyncio
async def test_regular_user_can_not_delete_user(authenticated_client_with_db, setup_users):
    client, _ = authenticated_client_with_db
    user1, user2, admin = setup_users

    for user in [user1, user2]:
        response = await client.delete(f"/users/admin/username/{user['username']}/")
        assert response.status_code == 403

    # Check that the user was not deleted using tortoise ORM
    for user in [user1, user2]:
        user_in_db = await User.filter(username=user["username"]).first()
        assert user_in_db == User(**user)

@pytest.mark.asyncio
async def test_regular_user_can_not_get_user_info(authenticated_client_with_db, setup_users):
    client, _ = authenticated_client_with_db
    user1, user2, admin = setup_users
    
    for endpoint, user in zip(["username", "email", "id"], [user1, user2]):
        val = user[endpoint]
        response = await client.get(f"/users/admin/{endpoint}/{val}/")
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_user_can_get_user_info(authenticated_admin_client_with_db, setup_users):
    client, _ = authenticated_admin_client_with_db
    user1, user2, admin = setup_users
    
    for endpoint, user in zip(["username", "email", "id"], [user1, user2]):
        val = user[endpoint]
        response = await client.get(f"/users/admin/{endpoint}/{val}/")
        assert response.status_code == 200
        response_dict = response.json()
        assert response_dict["id"] == user["id"]
        assert response_dict["username"] == user["username"]
        assert response_dict["email"] == user["email"]
        assert response_dict["full_name"] == user["full_name"]

@pytest.mark.asyncio
async def test_unauthenticated_user_can_not_get_user_info(test_app_with_db, setup_users):
    client, _, _, _ = test_app_with_db
    user1, user2, admin = setup_users

    for endpoint, user in zip(["username", "email", "id"], [user1, user2]):
        val = user[endpoint]
        response = await client.get(f"/users/admin/{endpoint}/{val}/")
        assert response.status_code == 401


#TODO: clean up this test
@pytest.mark.asyncio
async def test_authenticate_user(test_app_with_db, setup_users):
    client, _, _, _ = test_app_with_db
    user1, user2, admin = setup_users

    auth_payload = {
        "username": "wrong_username",
        "password": "wrong_password"
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

    auth_payload = {
        "username": user1["username"],
        "password": user1["password"]
    }

    # Create username and password form input
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

    auth_payload = {"username": user1["username"], "password": "wrong_password"}

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
    client, _, _, _ = test_app_with_db

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