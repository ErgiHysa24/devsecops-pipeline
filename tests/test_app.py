import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def add(client, title, body=""):
    return client.post("/notes", json={"title": title, "body": body})


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_create_and_get(client):
    r = add(client, "Spesa", "latte, pane")
    assert r.status_code == 201
    note_id = r.get_json()["id"]
    r = client.get(f"/notes/{note_id}")
    assert r.get_json()["body"] == "latte, pane"


def test_list_notes(client):
    add(client, "uno")
    add(client, "due")
    assert len(client.get("/notes").get_json()) == 2


def test_search(client):
    add(client, "riunione lunedì")
    add(client, "spesa")
    results = client.get("/notes?q=riunione").get_json()
    assert [n["title"] for n in results] == ["riunione lunedì"]


def test_title_required(client):
    assert client.post("/notes", json={"body": "x"}).status_code == 400
    assert add(client, "   ").status_code == 400


def test_too_long_rejected(client):
    assert add(client, "x" * 201).status_code == 400


def test_not_found(client):
    assert client.get("/notes/999").status_code == 404


def test_delete(client):
    note_id = add(client, "da cancellare").get_json()["id"]
    assert client.delete(f"/notes/{note_id}").status_code == 204
    assert client.get(f"/notes/{note_id}").status_code == 404


def test_search_is_not_sql_injectable(client):
    """A classic payload must be treated as text, not as SQL."""
    add(client, "segreta", "non dovresti vedermi")
    payload = "' OR '1'='1"
    r = client.get("/notes", query_string={"q": payload})
    assert r.status_code == 200
    assert r.get_json() == []
