import pytest

from app.api import summaries


@pytest.mark.asyncio
async def test_create_summary(test_app_with_db, monkeypatch):
    client, _, _, _ = test_app_with_db
    def mock_generate_summary(summary_id, url):
        return None
    monkeypatch.setattr(summaries, "generate_summary", mock_generate_summary)

    response = await client.post(
        "/summaries/", json={"url": "https://foo.bar"}
    )

    assert response.status_code == 201
    assert response.json()["url"] == "https://foo.bar/"

def test_create_summaries_invalid_json(test_app):
    response = test_app.post("/summaries/", json={})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "input": {},
                "loc": ["body", "url"],
                "msg": "Field required",
                "type": "missing",
            }
        ]
    }

    response = test_app.post("/summaries/", json={"url": "invalid://url"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "URL scheme should be 'http' or 'https'"

@pytest.mark.asyncio
async def test_read_summary(test_app_with_db, monkeypatch):
    client, _, _, _ = test_app_with_db
    def mock_generate_summary(summary_id, url):
        return None
    monkeypatch.setattr(summaries, "generate_summary", mock_generate_summary)

    response = await client.post("/summaries/", json={"url": "https://foo.bar/"})
    summary_id = response.json()["id"]

    response = await client.get(f"/summaries/{summary_id}/")
    assert response.status_code == 200

    response_dict = response.json()
    assert response_dict["id"] == summary_id
    assert response_dict["url"] == "https://foo.bar/"
    assert response_dict["summary"] == ''
    assert response_dict["created_at"]


@pytest.mark.asyncio
async def test_read_summary_incorrect_id(test_app_with_db):
    client, _, _, _ = test_app_with_db
    response = await client.get("/summaries/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Summary not found"

    response = await client.get("/summaries/0/")
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
async def test_read_all_summaries(test_app_with_db, monkeypatch):
    client, _, _, _ = test_app_with_db
    def mock_generate_summary(summary_id, url):
        return None
    monkeypatch.setattr(summaries, "generate_summary", mock_generate_summary)

    response = await client.post("/summaries/", json={"url": "https://foo.bar/"})
    summary_id = response.json()["id"]

    response = await client.get("/summaries/")
    assert response.status_code == 200

    response_list = response.json()
    assert len(list(filter(lambda d: d["id"] == summary_id, response_list))) == 1

@pytest.mark.asyncio
async def test_remove_summary(test_app_with_db, monkeypatch):
    client, _, _, _ = test_app_with_db
    def mock_generate_summary(summary_id, url):
        return None
    monkeypatch.setattr(summaries, "generate_summary", mock_generate_summary)

    response = await client.post("/summaries/", json={"url": "https://foo.bar/"})
    summary_id = response.json()["id"]

    response = await client.delete(f"/summaries/{summary_id}/")
    assert response.status_code == 200
    assert response.json() == {"id": summary_id, "url": "https://foo.bar/"}


@pytest.mark.asyncio
async def test_remove_summary_incorrect_id(test_app_with_db):
    client, _, _, _ = test_app_with_db
    response = await client.delete("/summaries/999/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Summary not found"

    response = await client.delete("/summaries/0/")
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
async def test_update_summary(test_app_with_db, monkeypatch):
    client, _, _, _ = test_app_with_db
    def mock_generate_summary(summary_id, url):
        return None

    monkeypatch.setattr(summaries, "generate_summary", mock_generate_summary)

    response = await client.post("/summaries/", json={"url": "https://foo.bar/"})
    summary_id = response.json()["id"]

    response = await client.put(
        f"/summaries/{summary_id}/",
        json={"url": "https://foo.bar/", "summary": "updated!"},
    )
    assert response.status_code == 200

    response_dict = response.json()
    assert response_dict["id"] == summary_id
    assert response_dict["url"] == "https://foo.bar/"
    assert response_dict["summary"] == "updated!"
    assert response_dict["created_at"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "summary_id, payload, status_code, detail",
    [
        [
            999,
            {"url": "https://foo.bar/", "summary": "updated!"},
            404,
            "Summary not found",
        ],
        [
            0,
            {"url": "https://foo.bar/", "summary": "updated!"},
            422,
            [
                {
                    "type": "greater_than",
                    "loc": ["path", "id"],
                    "msg": "Input should be greater than 0",
                    "input": "0",
                    "ctx": {"gt": 0},
                }
            ],
        ],
        [
            1,
            {},
            422,
            [
                {
                    "type": "missing",
                    "loc": ["body", "url"],
                    "msg": "Field required",
                    "input": {},
                },
                {
                    "type": "missing",
                    "loc": ["body", "summary"],
                    "msg": "Field required",
                    "input": {},
                },
            ],
        ],
        [
            1,
            {"url": "https://foo.bar/"},
            422,
            [
                {
                    "type": "missing",
                    "loc": ["body", "summary"],
                    "msg": "Field required",
                    "input": {"url": "https://foo.bar/"},
                }
            ],
        ],
    ],
)
async def test_update_summary_invalid(
    test_app_with_db, summary_id, payload, status_code, detail
):
    client, _, _, _ = test_app_with_db
    response = await client.put(f"/summaries/{summary_id}/", json=payload)
    assert response.status_code == status_code
    assert response.json()["detail"] == detail


def test_update_summary_invalid_url(test_app):
    response = test_app.put(
        "/summaries/1/",
        json={"url": "invalid://url", "summary": "updated!"},
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"][0]["msg"] == "URL scheme should be 'http' or 'https'"
    )