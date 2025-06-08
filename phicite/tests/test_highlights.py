import pytest
from app.models.tortoise import PDFHighlight
from app.api.users import get_current_user

highlight_json = {
    "doi": "10.1234/example.5678",
    "highlight": {
        "1": {"rect": [100, 200, 300, 220], "text": "first part"},
        "2": {"rect": [50, 100, 250, 120], "text": "second part"}
        },
    "comment": "This is an important passage"
}

@pytest.mark.asyncio
async def test_authenticated_user_can_create_highlight_with_valid_json(
    authenticated_client_with_db,
):

    client, new_user = authenticated_client_with_db

    response = await client.post(
        "/highlights/",
        json=highlight_json
    )

    assert response.status_code == 201
    response_dict = response.json()
    assert response_dict.keys() == {"id", "doi", "created_at"}
    assert response_dict["doi"] == highlight_json["doi"]

    highlight_id = response_dict["id"]
    highlight = await PDFHighlight.get(id=highlight_id)
    
    assert highlight.doi == highlight_json["doi"]
    assert highlight.highlight == highlight_json["highlight"]
    assert highlight.comment == highlight_json["comment"]
    await highlight.fetch_related("user")
    assert highlight.user.username == new_user["username"]


@pytest.mark.asyncio
async def test_unauthenticated_user_cannot_create_highlight(test_app_with_db):
    client, _, _ = test_app_with_db
    response = await client.post(
        "/highlights/",
        json=highlight_json
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_user_can_not_create_highlight_with_invalid_json(authenticated_client_with_db):
    client, _ = authenticated_client_with_db
    response = await client.post("/highlights/", json={})
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
    response = await client.post(
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
async def test_authenticated_user_can_read_highlight(authenticated_client_with_db, test_highlights):
    client, _ = authenticated_client_with_db

    single_highlight = test_highlights["single_highlight"]

    response = await client.get(f"/highlights/{single_highlight['id']}/")
    assert response.status_code == 200
    response_dict = response.json()
    for key in response_dict.keys():
        assert response_dict[key] == single_highlight[key]
    assert "username" in response_dict.keys()

@pytest.mark.asyncio
async def test_unauthenticated_user_can_not_read_highlight(test_app_with_db, test_highlights):

    client, _, _ = test_app_with_db

    single_highlight = test_highlights["single_highlight"]

    client.headers.pop("Authorization", None)

    response = await client.get(f"/highlights/{single_highlight['id']}/")
    assert response.status_code == 401
    

@pytest.mark.asyncio
async def test_unauthenticated_user_can_read_public_highlight(test_app_with_db, test_highlights):

    client, _, _ = test_app_with_db

    single_highlight = test_highlights["single_highlight"]

    client.headers.pop("Authorization", None)

    response = await client.get(f"/highlights/{single_highlight['id']}/public")
    assert response.status_code == 200
    response_dict = response.json()
    for key in response_dict.keys():
        assert response_dict[key] == single_highlight[key]
    assert "username" not in response_dict.keys()


@pytest.mark.asyncio
async def test_unauthenticated_user_tries_to_read_highlight_with_incorrect_id(test_app_with_db):

    client, _, _ = test_app_with_db

    client.headers.pop("Authorization", None)

    response = await client.get("/highlights/999/public")
    assert response.status_code == 404
    assert response.json()["detail"] == "highlight not found"

    response = await client.get("/highlights/0/public")
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
async def test_authenticated_user_tries_to_read_highlight_with_incorrect_id(authenticated_client_with_db):

    client, _ = authenticated_client_with_db

    response = await client.get("/highlights/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "highlight not found"

    response = await client.get("/highlights/0/")
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
async def test_authenticated_user_can_read_all_highlights(
    authenticated_client_with_db, test_highlights
):
    client, _ = authenticated_client_with_db 
    single_highlight = test_highlights["single_highlight"]
    another_user_highlight = test_highlights["another_user_highlight"]
    multiple_highlights = test_highlights["multiple_highlights"]
    all_highlights = [single_highlight] + [another_user_highlight] + multiple_highlights
    response = await client.get("/highlights/")
    assert response.status_code == 200
    response_list = response.json()
    assert len(response_list) == len(all_highlights)
    for i, highlight in enumerate(all_highlights):
        for key in response_list[i].keys():
            assert response_list[i][key] == highlight[key]

@pytest.mark.asyncio
async def test_unauthenticated_user_can_read_all_public_highlights(
    test_app_with_db, test_highlights
):
    client, _, _ = test_app_with_db
    single_highlight = test_highlights["single_highlight"]
    another_user_highlight = test_highlights["another_user_highlight"]
    multiple_highlights = test_highlights["multiple_highlights"]
    all_highlights = [single_highlight] + [another_user_highlight] + multiple_highlights
    client.headers.pop("Authorization", None)
    response = await client.get("/highlights/public")
    assert response.status_code == 200
    response_list = response.json()
    assert len(response_list) == len(all_highlights)
    for i, highlight in enumerate(all_highlights):
        for key in response_list[i].keys():
            assert response_list[i][key] == highlight[key]
        assert "username" not in response_list[i]


@pytest.mark.asyncio
async def test_authenticated_user_can_remove_their_highlight(
    authenticated_client_with_db, test_highlights
):
    client, _ = authenticated_client_with_db
    single_highlight = test_highlights["single_highlight"]

    response = await client.delete(f"/highlights/{single_highlight['id']}/")
    assert response.status_code == 200
    for key in response.json().keys():
        assert response.json()[key] == single_highlight[key]

@pytest.mark.asyncio
async def test_authenticated_user_can_not_remove_another_user_highlight(
    authenticated_client_with_db, test_highlights
):
    client, user = authenticated_client_with_db
    another_user_highlight = test_highlights["another_user_highlight"]

    token = client.headers["Authorization"].split(" ")[1]
    current_user = await get_current_user(token)
    assert current_user.username == user["username"]

    assert another_user_highlight["username"] != user["username"]
    print(f"another_user_highlight[username]: {another_user_highlight["username"]}")
    print(f"user[username]: {user['username']}")

    response = await client.delete(f"/highlights/{another_user_highlight['id']}/")
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to delete this highlight"


@pytest.mark.asyncio
async def test_authenticated_user_tries_to_remove_highlight_with_incorrect_id(
    authenticated_client_with_db,
):
    client, _ = authenticated_client_with_db
    response = await client.delete("/highlights/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "highlight not found"

    response = await client.delete("/highlights/0/")
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
async def test_unauthenticated_user_can_not_remove_highlight(
    test_app_with_db, test_highlights
):
    client, _, _ = test_app_with_db
    single_highlight = test_highlights["single_highlight"]
    client.headers.pop("Authorization", None)
    response = await client.delete(f"/highlights/{single_highlight['id']}/")
    assert response.status_code == 401
    highlight = await PDFHighlight.get(id=single_highlight["id"])
    assert highlight.id == single_highlight["id"]


@pytest.mark.asyncio
async def test_authenticated_user_can_update_their_highlight(
    authenticated_client_with_db, test_highlights
):
    client, _ = authenticated_client_with_db
    single_highlight = test_highlights["single_highlight"]
    update_payload = {
        "doi": "10.1234/example.5678",
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "updated highlight"}},
        "comment": "Updated comment",
    }
    response = await client.put(f"/highlights/{single_highlight['id']}/", json=update_payload)
    assert response.status_code == 200
    updated_highlight = await PDFHighlight.get(id=single_highlight["id"])
    assert updated_highlight.highlight == update_payload["highlight"]
    assert updated_highlight.comment == update_payload["comment"]

#TODO: test authenticated user cannot update another user highlight

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
async def test_authenticated_user_tries_to_update_highlight_with_invalid_payloads(
    authenticated_client_with_db, id, payload, status_code, detail
):
    client, _ = authenticated_client_with_db
    response = await client.put(f"/highlights/{id}/", json=payload)
    assert response.status_code == status_code
    if isinstance(detail, str):
        assert response.json()["detail"] == detail
    else:
        assert response.json() == {"detail": detail}


@pytest.mark.asyncio
async def test_authenticated_user_tries_to_update_highlight_with_doi_not_matching(
    authenticated_client_with_db, test_highlights
):
    client, _ = authenticated_client_with_db
    single_highlight = test_highlights["single_highlight"]
    
    update_payload = {
        "doi": "10.9876/example.5432",  # Different DOI
        "highlight": {"1": {"rect": [100, 200, 300, 220], "text": "updated highlight"}},
        "comment": "Updated comment",
    }

    response = await client.put(f"/highlights/{single_highlight['id']}/", json=update_payload)
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