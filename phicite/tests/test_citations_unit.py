import json

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