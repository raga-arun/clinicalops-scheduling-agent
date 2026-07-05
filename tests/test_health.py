def test_health_success_envelope(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["statusCode"] == 200
    assert body["data"]["status"] == "ok"


def test_chat_success_envelope(client, tenant_headers):
    resp = client.post("/api/v1/chat", json={"message": "hi"}, headers=tenant_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["data"]["intent"] == "unknown"
    assert "sessionId" in body["data"]


def test_chat_root_level_ui_directives(client, tenant_headers):
    resp = client.post("/api/v1/chat", json={"message": "hi"}, headers=tenant_headers)
    assert resp.status_code == 200
    body = resp.json()
    # ui_directives sits alongside `data` at the envelope root, not inside data.
    assert "uiDirectives" not in body["data"]
    assert body["uiDirectives"] == {
        "showSelections": False,
        "showCalendly": False,
        "showRating": False,
        "showReasonForVisit": False,
        "showInsuranceUpload": False,
    }


def test_openapi_documents_enveloped_success(client):
    schema = client.get("/openapi.json").json()
    chat_op = schema["paths"]["/api/v1/chat"]["post"]
    ok_schema = chat_op["responses"]["200"]["content"]["application/json"]["schema"]
    ref = ok_schema.get("$ref", "")
    name = ref.rsplit("/", 1)[-1]
    props = schema["components"]["schemas"][name]["properties"]
    # Envelope shape is generated natively by FastAPI, extras included.
    assert {"status", "statusCode", "message", "data", "uiDirectives"} <= props.keys()


def test_missing_tenant_error_envelope(client):
    resp = client.post("/api/v1/chat", json={"message": "hi"})
    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == "error"
    assert body["errorCode"] == "MISSING_TENANT"
    assert body["path"] == "/api/v1/chat"


def test_validation_error_envelope(client, tenant_headers):
    resp = client.post("/api/v1/chat", json={}, headers=tenant_headers)
    assert resp.status_code == 400
    body = resp.json()
    assert body["status"] == "error"
    assert body["errorCode"] == "BAD_REQUEST"
    assert body["errors"][0]["field"] == "message"


def test_not_found_error_envelope(client, tenant_headers):
    resp = client.get("/api/v1/nope", headers=tenant_headers)
    assert resp.status_code == 404
    body = resp.json()
    assert body["status"] == "error"
    assert body["errorCode"] == "NOT_FOUND"


def test_method_not_allowed_error_envelope(client, tenant_headers):
    resp = client.get("/api/v1/chat", headers=tenant_headers)
    assert resp.status_code == 405
    body = resp.json()
    assert body["status"] == "error"
    assert body["errorCode"] == "METHOD_NOT_ALLOWED"
