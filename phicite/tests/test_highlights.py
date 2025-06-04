import pytest


@pytest.mark.asyncio
async def test_create_highlight_valid_json(test_app_with_db):
    """Integration test for creating a highlight with valid JSON."""
    response = await test_app_with_db.post(
        "/highlights/",
        json={
            "doi": "10.1234/example.5678",
            "highlight": {
                "1": {"rect": [100, 200, 300, 220], "text": "first part"},
                "2": {"rect": [50, 100, 250, 120], "text": "second part"}
                },
            "comment": "This is an important passage"
        }
    )

    assert response.status_code == 201
    response_dict = response.json()
    assert response_dict["doi"] == "10.1234/example.5678"
    assert "id" in response_dict


@pytest.mark.asyncio
async def test_create_highlight_invalid_json(test_app_with_db):
    """Integration test for creating a highlight with invalid JSON."""
    # Test with empty JSON
    response = await test_app_with_db.post("/highlights/", json={})
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
    response = await test_app_with_db.post(
        "/highlights/",
        json={
            "doi": "invalid-doi",
            "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "highlighted text"}}
        }
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

@pytest.mark.asyncio
async def test_read_highlight(test_app_with_db):
    response = await test_app_with_db.post(
        "/highlights/",
        json={
            "doi": "10.1234/example.5678",
            "highlight": {
                "1": {"rect": [100, 200, 300, 220], "text": "first part"},
                "2": {"rect": [50, 100, 250, 120], "text": "second part"},
            },
            "comment": "This is an important passage",
        },
    )
    assert response.status_code == 201
    highlight_id = response.json()["id"]
    response = await test_app_with_db.get(f"/highlights/{highlight_id}/")
    assert response.status_code == 200
    response_dict = response.json()
    assert response_dict["id"] == highlight_id
    assert response_dict["doi"] == "10.1234/example.5678"
    assert response_dict["comment"] == "This is an important passage"
    assert "highlight" in response_dict


@pytest.mark.asyncio
async def test_read_highlight_incorrect_id(test_app_with_db):
    response = await test_app_with_db.get("/highlights/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "highlight not found"

    response = await test_app_with_db.get("/highlights/0/")
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


@pytest.mark.asyncio
async def test_read_all_highlights(test_app_with_db, monkeypatch):
    response = await test_app_with_db.post(
        "/highlights/",
        json={
            "doi": "10.1234/example.5678",
            "highlight": {
                "1": {"rect": [100, 200, 300, 220], "text": "first part"},
                "2": {"rect": [50, 100, 250, 120], "text": "second part"},
            },
            "comment": "This is an important passage",
        },
    )
    assert response.status_code == 201
    highlight_id = response.json()["id"]
    response = await test_app_with_db.get("/highlights/")
    assert response.status_code == 200
    response_list = response.json()
    assert len(list(filter(lambda d: d["id"] == highlight_id, response_list))) == 1


@pytest.mark.asyncio
async def test_remove_highlight(test_app_with_db):
    response = await test_app_with_db.post(
        "/highlights/",
        json={
            "doi": "10.1234/example.5678",
            "highlight": {
                "1": {"rect": [100, 200, 300, 220], "text": "first part"},
                "2": {"rect": [50, 100, 250, 120], "text": "second part"},
            },
            "comment": "This is an important passage",
        },
    )
    assert response.status_code == 201
    highlight_id = response.json()["id"]

    response = await test_app_with_db.delete(f"/highlights/{highlight_id}/")
    assert response.status_code == 200
    assert response.json() == {"id": highlight_id, "doi": "10.1234/example.5678"}


@pytest.mark.asyncio
async def test_remove_highlight_incorrect_id(test_app_with_db):
    response = await test_app_with_db.delete("/highlights/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "highlight not found"

    response = await test_app_with_db.delete("/highlights/0/")
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


@pytest.mark.asyncio
async def test_update_highlight(test_app_with_db):
    response = await test_app_with_db.post(
        "/highlights/",
        json=
            {
                "doi": "10.1234/example.5678",
                "highlight": {
                    "1": {"rect": [100, 200, 300, 220], "text": "first part"},
                    "2": {"rect": [50, 100, 250, 120], "text": "second part"},
                },
                "comment": "This is an important passage",
            }
    )
    assert response.status_code == 201
    highlight_id = response.json()["id"]

    update_payload = {
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "updated highlight"}},
        "comment": "Updated comment",
    }
    response = await test_app_with_db.put(f"/highlights/{highlight_id}/", json=update_payload)
    assert response.status_code == 200
    updated_highlight = response.json()
    assert updated_highlight["id"] == highlight_id
    assert updated_highlight["highlight"]["1"]["text"] == "updated highlight"
    assert updated_highlight["comment"] == "Updated comment"


@pytest.mark.asyncio
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
            "highlight not found",
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
async def test_update_highlight_invalid(test_app_with_db, id, payload, status_code, detail):
    response = await test_app_with_db.put(f"/highlights/{id}/", json=payload)
    assert response.status_code == status_code
    if isinstance(detail, str):
        assert response.json()["detail"] == detail
    else:
        assert response.json() == {"detail": detail}


@pytest.mark.asyncio
async def test_update_highlight_doi_not_matching(test_app_with_db):
    response = await test_app_with_db.post(
        "/highlights/",
            json=
            {
                "doi": "10.1234/example.5678",
                "highlight": {
                    "1": {"rect": [100, 200, 300, 220], "text": "first part"},
                    "2": {"rect": [50, 100, 250, 120], "text": "second part"},
                },
                "comment": "This is an important passage",
            }
    )
    assert response.status_code == 201
    highlight_id = response.json()["id"]

    update_payload = {
        "doi": "10.9876/example.5432",  # Different DOI
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "updated highlight"}},
        "comment": "Updated comment",
    }
    response = await test_app_with_db.put(f"/highlights/{highlight_id}/", json=update_payload)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "ctx": {"error": {}},
                "loc": ["body", "doi"],
                "msg": "Value error, DOI does not match existing highlight",
                "type": "value_error",
            }
        ]
    }