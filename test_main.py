import pytest
from fastapi.testclient import TestClient

from main import app, store

client = TestClient(app)

GRAPHQL = {
    "name": "GraphQL",
    "category": "Backend",
    "proficiency": 2,
    "status": "learning",
    "notes": "Comparing it with REST",
}


@pytest.fixture(autouse=True)
def reset_data():
    # start every test with the 3 sample skills
    store.reset()


def test_home():
    res = client.get("/")
    assert res.status_code == 200
    assert "create_skill" in res.json()["endpoints"]


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_list_skills():
    res = client.get("/api/v1/skills")
    assert res.status_code == 200
    assert res.json()["meta"]["total"] == 3
    assert len(res.json()["data"]) == 3


def test_filters_and_paging():
    assert client.get("/api/v1/skills?status=mastered").json()["meta"]["total"] == 1
    assert client.get("/api/v1/skills?category=backend").json()["meta"]["total"] == 1
    assert client.get("/api/v1/skills?q=docker").json()["data"][0]["name"] == "Docker"

    page = client.get("/api/v1/skills?limit=2&offset=2").json()
    assert page["meta"] == {"total": 3, "count": 1, "limit": 2, "offset": 2}


def test_get_one():
    assert client.get("/api/v1/skills/1").json()["data"]["id"] == 1

    res = client.get("/api/v1/skills/999")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"


def test_create():
    res = client.post("/api/v1/skills", json=GRAPHQL)
    assert res.status_code == 201
    assert res.headers["location"] == "/api/v1/skills/4"
    assert res.json()["data"]["name"] == "GraphQL"


def test_create_bad_proficiency():
    res = client.post("/api/v1/skills", json={**GRAPHQL, "proficiency": 9})
    assert res.status_code == 422
    assert res.json()["error"]["details"][0]["field"] == "proficiency"


def test_create_extra_field():
    res = client.post("/api/v1/skills", json={**GRAPHQL, "favorite": True})
    assert res.status_code == 422


def test_create_duplicate():
    res = client.post("/api/v1/skills", json={**GRAPHQL, "name": "python"})
    assert res.status_code == 409


def test_put():
    before = client.get("/api/v1/skills/3").json()["data"]
    res = client.put("/api/v1/skills/3", json={**GRAPHQL, "name": "Docker & Compose"})
    after = res.json()["data"]

    assert res.status_code == 200
    assert after["name"] == "Docker & Compose"
    assert after["category"] == "Backend"
    assert after["created_at"] == before["created_at"]


def test_put_missing_fields():
    res = client.put("/api/v1/skills/3", json={"name": "Only a name"})
    assert res.status_code == 422


def test_patch():
    res = client.patch("/api/v1/skills/1", json={"proficiency": 5, "status": "mastered"})
    assert res.status_code == 200
    assert res.json()["updated_fields"] == ["proficiency", "status"]
    assert res.json()["data"]["name"] == "REST API design"


def test_patch_empty():
    assert client.patch("/api/v1/skills/1", json={}).status_code == 400


def test_patch_null():
    assert client.patch("/api/v1/skills/1", json={"name": None}).status_code == 400


def test_delete():
    res = client.delete("/api/v1/skills/2")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Python"

    assert client.get("/api/v1/skills/2").status_code == 404
    assert client.delete("/api/v1/skills/2").status_code == 404


def test_unknown_route():
    res = client.get("/nope")
    assert res.status_code == 404
    assert res.json()["error"]["message"] == "Route not found."


def test_wrong_method():
    res = client.delete("/api/v1/skills")
    assert res.status_code == 405
    assert res.json()["error"]["code"] == "method_not_allowed"
