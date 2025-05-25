import json


def test_create_citation_valid_json(test_app_with_db):
    """Integration test for creating a citation with valid JSON."""
    response = test_app_with_db.post(
        "/citations/",
        data=json.dumps({
            "doi": "10.1234/example.5678",
            "highlight": {
                "1": {"rect": [100, 200, 300, 220], "text": "first part"},
                "2": {"rect": [50, 100, 250, 120], "text": "second part"}
                },
            "comment": "This is an important passage"
        })
    )

    assert response.status_code == 201
    response_dict = response.json()
    assert response_dict["doi"] == "10.1234/example.5678"
    assert "id" in response_dict


def test_create_citation_invalid_json(test_app_with_db):
    """Integration test for creating a citation with invalid JSON."""
    # Test with empty JSON
    response = test_app_with_db.post("/citations/", data=json.dumps({}))
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": {},
                "loc": ["body", "doi"],
                "msg": "Field required",
                "type": "missing",
            },
            {
                "input": {},
                "loc": ["body", "highlight"],
                "msg": "Field required",
                "type": "missing",
            }
        ]
    }

    # Test with invalid DOI format
    response = test_app_with_db.post(
        "/citations/",
        data=json.dumps({
            "doi": "invalid-doi",
            "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}}
        })
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "ctx": {"error": {}},
                "input": "invalid-doi",
                "loc": ["body", "doi"],
                "msg": "Value error, Invalid DOI format",
                "type": "value_error",
            }
        ]
    }

def test_read_citation(test_app_with_db):
    response = test_app_with_db.post(
        "/citations/",
        data=json.dumps({
            "doi": "10.1234/example.5678",
            "highlight": {
                "1": {"rect": [100, 200, 300, 220], "text": "first part"},
                "2": {"rect": [50, 100, 250, 120], "text": "second part"}
            },
            "comment": "This is an important passage"
        })
    )
    assert response.status_code == 201
    citation_id = response.json()["id"]
    response = test_app_with_db.get(f"/citations/{citation_id}/")
    assert response.status_code == 200
    response_dict = response.json()
    assert response_dict["id"] == citation_id
    assert response_dict["doi"] == "10.1234/example.5678"
    assert response_dict["comment"] == "This is an important passage"
    assert "highlight" in response_dict