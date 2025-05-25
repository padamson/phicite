import json
import pytest


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

def test_read_citation_incorrect_id(test_app_with_db):
    response = test_app_with_db.get("/citations/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Citation not found"

    response = test_app_with_db.get("/citations/0/")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "ctx": {"gt": 0},
                "input": "0",
                "loc": ["path", "id"],
                "msg": "Input should be greater than 0",
                "type": "greater_than",
            }
        ]
    }

def test_read_all_citations(test_app_with_db, monkeypatch):

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
    response = test_app_with_db.get("/citations/")
    assert response.status_code == 200
    response_list = response.json()
    assert len(list(filter(lambda d: d["id"] == citation_id, response_list))) == 1

def test_remove_citation(test_app_with_db):
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

    response = test_app_with_db.delete(f"/citations/{citation_id}/")
    assert response.status_code == 200
    assert response.json() == {"id": citation_id, "doi": "10.1234/example.5678"}

def test_remove_citation_incorrect_id(test_app_with_db):
    response = test_app_with_db.delete("/citations/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Citation not found"

    response = test_app_with_db.delete("/citations/0/")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "ctx": {"gt": 0},
                "input": "0",
                "loc": ["path", "id"],
                "msg": "Input should be greater than 0",
                "type": "greater_than",
            }
        ]
    }

def test_update_citation(test_app_with_db):
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

    update_payload = {
        "doi": "10.1234/example.5678",
        "highlight": {
            "1": {"rect": [100, 200, 300, 220], "text": "updated highlight"}
        },
        "comment": "Updated comment"
    }
    response = test_app_with_db.put(f"/citations/{citation_id}/", data=json.dumps(update_payload))
    assert response.status_code == 200
    updated_citation = response.json()
    assert updated_citation["id"] == citation_id
    assert updated_citation["highlight"]["1"]["text"] == "updated highlight"
    assert updated_citation["comment"] == "Updated comment"

@pytest.mark.parametrize(
    "id, payload, status_code, detail",
    [
        (
            999,
            {
                "doi": "10.1234/example.5678",
                "highlight": {
                    "1": {"rect": [100, 200, 300, 220], "text": "first part"}
                },
            },
            404,
            "Citation not found",
        ),
        (
            0,
            {
                "doi": "10.1234/example.5678",
                "highlight": {
                    "1": {"rect": [100, 200, 300, 220], "text": "first part"}
                },
            },
            422,
            [
                {
                    "ctx": {"gt": 0},
                    "input": "0",
                    "loc": ["path", "id"],
                    "msg": "Input should be greater than 0",
                    "type": "greater_than",
                }
            ],
        ),
    ],
)
def test_update_citation_invalid(test_app_with_db, id, payload, status_code, detail):
    response = test_app_with_db.put(f"/citations/{id}/", data=json.dumps(payload))
    assert response.status_code == status_code
    if isinstance(detail, str):
        assert response.json()["detail"] == detail
    else:
        assert response.json() == {"detail": detail}


def test_update_citation_doi_not_matching(test_app_with_db):
    response = test_app_with_db.post(
        "/citations/",
        data=json.dumps(
            {
                "doi": "10.1234/example.5678",
                "highlight": {
                    "1": {"rect": [100, 200, 300, 220], "text": "first part"},
                    "2": {"rect": [50, 100, 250, 120], "text": "second part"},
                },
                "comment": "This is an important passage",
            }
        ),
    )
    assert response.status_code == 201
    citation_id = response.json()["id"]

    update_payload = {
        "doi": "10.9876/example.5432",  # Different DOI
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "updated highlight"}},
        "comment": "Updated comment",
    }
    response = test_app_with_db.put(
        f"/citations/{citation_id}/", data=json.dumps(update_payload)
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "ctx": {"error": {}},
                "loc": ["body", "doi"],
                "msg": "Value error, DOI does not match existing citation",
                "type": "value_error",
            }
        ]
    }