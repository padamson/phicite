import json
from datetime import datetime

from app.api import crud

def test_create_citation(test_app, monkeypatch):
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
    monkeypatch.setattr(crud, "post_citation", mock_post)

    response = test_app.post(
        "/citations/", 
        data=json.dumps(test_request_payload)
    )

    assert response.status_code == 201
    assert response.json() == test_response_payload


def test_read_citation(test_app, monkeypatch):
    test_data = {
        "id": 1,
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
        "comment": "This is an important passage",
        "created_at": datetime.utcnow().isoformat(),
    }

    async def mock_get(id):
        return test_data

    monkeypatch.setattr(crud, "get_citation", mock_get)

    response = test_app.get("/citations/1/")
    assert response.status_code == 200
    assert response.json() == test_data

def test_read_citation_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_citation", mock_get)

    response = test_app.get("/citations/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Citation not found"

def test_read_all_citations(test_app, monkeypatch):
    test_data = [
        {
            "id": 1,
            "doi": "10.1234/example.5678",
            "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
            "comment": "This is an important passage",
            "created_at": datetime.utcnow().isoformat(),
        },
        {
            "id": 2,
            "doi": "10.9876/example.5432",
            "highlight": {"1": {"rect": [50, 100, 250, 120], "text": "another highlight"}},
            "comment": "Another important passage",
            "created_at": datetime.utcnow().isoformat(),
        }
    ]

    async def mock_get_all():
        return test_data

    monkeypatch.setattr(crud, "get_all_citations", mock_get_all)

    response = test_app.get("/citations/")
    assert response.status_code == 200
    assert response.json() == test_data

def test_remove_citation(test_app, monkeypatch):
    async def mock_get(id):
        return {
            "id": id,
            "doi": "10.1234/example.5678",
            "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}},
            "comment": "This is an important passage",
            "created_at": datetime.utcnow().isoformat(),
        }
    monkeypatch.setattr(crud, "get_citation", mock_get)
    async def mock_delete(id):
        return id
    
    monkeypatch.setattr(crud, "delete_citation", mock_delete)
    response = test_app.delete("/citations/1/")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "doi": "10.1234/example.5678"}

def test_remove_citation_incorrect_id(test_app, monkeypatch):
    async def mock_get(id):
        return None

    monkeypatch.setattr(crud, "get_citation", mock_get)

    response = test_app.delete("/citations/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Citation not found"

def test_update_citation(test_app, monkeypatch):
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
        "created_at": datetime.utcnow().isoformat(),
    }
    async def mock_put(id, payload):
        return test_response_payload
    monkeypatch.setattr(crud, "put_citation", mock_put)
    response = test_app.put(
        "/citations/1/", 
        data=json.dumps(test_request_payload)
    )
    assert response.status_code == 200
    assert response.json() == test_response_payload