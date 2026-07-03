def test_health_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_requires_tenant(client):
    resp = client.post("/api/v1/chat", json={"message": "book me an appointment"})
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "missing_tenant"
