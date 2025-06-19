from tests.conftest import current_datetime_utc_z
from app.api import crud

def test_create_highlight_authenticated(
    test_app,
    monkeypatch,
    mock_get_user_by_token_data_user,
    mock_user,
    auth_headers,
    mock_jwt_decode_user,
):
    # 3. Mock post_highlight to avoid database access
    created_at = current_datetime_utc_z()
    async def mock_post_highlight(payload, user_id):
        return 1, created_at
    monkeypatch.setattr(crud, "post_highlight", mock_post_highlight)
    
    # Test request payload
    test_request_payload = {
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}}
    }
    
    # Expected response
    test_response_payload = {
        "id": 1,
        "doi": "10.1234/example.5678",
        "created_at": str(created_at)
    }
    
    # Make request with Authorization header
    response = test_app.post(
        "/highlights/",
        json=test_request_payload,
        headers=auth_headers
    )
    
    # Assertions
    assert response.status_code == 201
    assert response.json() == test_response_payload

def test_create_highlight_unauthenticated(
    test_app,
    monkeypatch,
    mock_get_user_by_token_data_user,
    mock_user,
    auth_headers,
    mock_jwt_decode_user,
):
    # Test request with minimum required fields
    test_request_payload = {
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}}
    }

    async def mock_post_highlight(payload):
        return 1
    monkeypatch.setattr(crud, "post_highlight", mock_post_highlight)

    response = test_app.post(
        "/highlights/", 
        json=test_request_payload
    )

    assert response.status_code == 401

def test_read_highlight_requires_authentication(
    test_app,
    monkeypatch,
    mock_get_user_by_token_data_user,
    mock_user,
    auth_headers,
    mock_jwt_decode_user,
):
    """Test that the /highlights/id/{id}/ endpoint requires authentication."""
    # Mock the get_highlight function to return data if called
    # This ensures any 401 is due to auth failing, not missing data
    test_data = {
        "id": 1,
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
        "comment": "This is an important passage",
        "username": "testuser",
        "created_at": current_datetime_utc_z(),
    }
    
    async def mock_get(id):
        return test_data
    
    monkeypatch.setattr(crud, "get_highlight", mock_get)
    
    # Make request without authentication
    response = test_app.get("/highlights/id/1/")
    
    # Assert that we get a 401 Unauthorized response
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Not authenticated" in response.json()["detail"]

    # 4. Make request with valid authentication
    response = test_app.get("/highlights/id/1/", headers=auth_headers)
    
    # Should now succeed
    assert response.status_code == 200
    assert response.json() == test_data

def test_read_highlight_incorrect_id(
    test_app,
    monkeypatch,
    mock_get_user_by_token_data_user,
    mock_user,
    auth_headers,
    mock_jwt_decode_user,
):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_highlight", mock_get)

    response = test_app.get("/highlights/id/999/", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "highlight not found"

def test_read_all_highlights(
    test_app,
    monkeypatch,
    mock_get_user_by_token_data_user,
    mock_user,
    auth_headers,
    mock_jwt_decode_user,
):
    test_data = [
        {
            "id": 1,
            "doi": "10.1234/example.5678",
            "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
            "comment": "This is an important passage",
            "username": "testuser",
            "created_at": current_datetime_utc_z(),
        },
        {
            "id": 2,
            "doi": "10.9876/example.5432",
            "highlight": {"1": {"rect": [50, 100, 250, 120], "text": "another highlight"}},
            "comment": "Another important passage",
            "username": "testuser",
            "created_at": current_datetime_utc_z(),
        }
    ]

    async def mock_get_all():
        return test_data

    monkeypatch.setattr(crud, "get_all_highlights", mock_get_all)

    response = test_app.get("/highlights/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == test_data

def test_remove_highlight(
    test_app,
    monkeypatch,
    mock_get_user_by_token_data_user,
    mock_user,
    auth_headers,
    mock_jwt_decode_user,
):
    id = 1
    async def mock_delete_highlight(id, user_id):
        return {"id": id}
    
    monkeypatch.setattr(crud, "delete_highlight", mock_delete_highlight)
    response = test_app.delete(f"/highlights/id/{id}/", headers=auth_headers)
    assert response.status_code == 200

def test_remove_highlight_incorrect_id(
    test_app,
    monkeypatch,
    mock_get_user_by_token_data_user,
    mock_user,
    auth_headers,
    mock_jwt_decode_user,
):

    async def mock_delete_highlight(id, user_id):
        return None
    
    monkeypatch.setattr(crud, "delete_highlight", mock_delete_highlight)

    response = test_app.delete("/highlights/id/999/", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "highlight not found"

def test_update_highlight(
    test_app,
    monkeypatch,
    mock_get_user_by_token_data_user,
    mock_user,
    auth_headers,
    mock_jwt_decode_user,
):
    test_request_payload = {
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
        "comment": "Updated comment"
    }
    test_response_payload = {
        "id": 1,
        "doi": "10.1234/example.5678",
        "created_at": current_datetime_utc_z(),
    }
    async def mock_put(id, payload, user_id):
        return test_response_payload
    monkeypatch.setattr(crud, "put_highlight", mock_put)
    response = test_app.put(
        "/highlights/id/1/", 
        json=test_request_payload,
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json() == test_response_payload