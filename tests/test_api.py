import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from omnicanon.api.app import app  # noqa: E402

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_search_endpoint():
    resp = client.get("/search", params={"q": "let there be light"})
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "kjv:genesis.1.3"


def test_verse_endpoint_404():
    assert client.get("/verse/kjv:genesis.1.999").status_code == 404


def test_verify_endpoint_catches_hallucination():
    resp = client.post("/verify", json={"text": "See [kjv:genesis.1.999]."})
    body = resp.json()
    assert not body["verified"]
    assert body["hallucinated_refs"] == ["kjv:genesis.1.999"]


def test_answer_endpoint_is_verified():
    resp = client.get("/answer", params={"q": "What did God create in the beginning?"})
    body = resp.json()
    assert body["verified"] is True
    assert body["mode"] == "extractive"
