from tests.conftest import current_datetime_utc_z
from app.api import crud

def test_create_highlight(test_app, monkeypatch):
    # Test request with minimum required fields
    test_request_payload = {
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}}
    }
    test_response_payload = {
        "id": 1,
        "doi": "10.1234/example.5678"
    }

    async def mock_post(payload):
        return 1
    monkeypatch.setattr(crud, "post_highlight", mock_post)

    response = test_app.post(
        "/highlights/", 
        json=test_request_payload
    )

    assert response.status_code == 201
    assert response.json() == test_response_payload


def test_read_highlight(test_app, monkeypatch):
    test_data = {
        "id": 1,
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
        "comment": "This is an important passage",
        "created_at": current_datetime_utc_z(),
    }

    async def mock_get(id):
        return test_data

    monkeypatch.setattr(crud, "get_highlight", mock_get)

    response = test_app.get("/highlights/1/")
    assert response.status_code == 200
    assert response.json() == test_data

def test_read_highlight_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_highlight", mock_get)

    response = test_app.get("/highlights/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "highlight not found"

def test_read_all_highlights(test_app, monkeypatch):
    test_data = [
        {
            "id": 1,
            "doi": "10.1234/example.5678",
            "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
            "comment": "This is an important passage",
            "created_at": current_datetime_utc_z(),
        },
        {
            "id": 2,
            "doi": "10.9876/example.5432",
            "highlight": {"1": {"rect": [50, 100, 250, 120], "text": "another highlight"}},
            "comment": "Another important passage",
            "created_at": current_datetime_utc_z(),
        }
    ]

    async def mock_get_all():
        return test_data

    monkeypatch.setattr(crud, "get_all_highlights", mock_get_all)

    response = test_app.get("/highlights/")
    assert response.status_code == 200
    assert response.json() == test_data

def test_remove_highlight(test_app, monkeypatch):
    id = 2
    doi = "10.1234/example.5678"
    async def mock_get(id):
        return {
            "id": id,
            "doi": doi,
            "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
            "comment": "This is an important passage",
            "created_at": current_datetime_utc_z(),
        }
    monkeypatch.setattr(crud, "get_highlight", mock_get)
    async def mock_delete(id):
        return 1
    
    monkeypatch.setattr(crud, "delete_highlight", mock_delete)
    response = test_app.delete(f"/highlights/{id}/")
    assert response.status_code == 200
    assert response.json() == {"id": id, "doi": doi}

def test_remove_highlight_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_highlight", mock_get)

    response = test_app.delete("/highlights/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "highlight not found"

def test_update_highlight(test_app, monkeypatch):
    test_request_payload = {
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
        "comment": "Updated comment"
    }
    test_response_payload = {
        "id": 1,
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
        "comment": "Updated comment",
        "created_at": current_datetime_utc_z(),
    }
    async def mock_put(id, payload):
        return test_response_payload
    monkeypatch.setattr(crud, "put_highlight", mock_put)
    response = test_app.put(
        "/highlights/1/", 
        json=test_request_payload
    )
    assert response.status_code == 200
    assert response.json() == test_response_payload