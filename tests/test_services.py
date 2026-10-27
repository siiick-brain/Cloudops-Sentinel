from fastapi.testclient import TestClient

from app import api, backend, mock_jira, mock_slack


def test_api_health_and_readiness(monkeypatch):
    client = TestClient(api.app)
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").status_code == 200
    monkeypatch.setenv("API_UNREADY", "1")
    assert client.get("/readyz").status_code == 503


def test_api_order_and_upstream_failure(monkeypatch):
    class GoodResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"sku": "demo", "available": True}

    monkeypatch.setattr(api.requests, "get", lambda *args, **kwargs: GoodResponse())
    client = TestClient(api.app)
    assert client.get("/orders/demo").json()["inventory"]["sku"] == "demo"

    def fail(*args, **kwargs):
        raise api.requests.Timeout("timeout")

    monkeypatch.setattr(api.requests, "get", fail)
    assert client.get("/orders/demo").status_code == 503


def test_api_chaos_auth_bounds_and_clear(monkeypatch):
    monkeypatch.setenv("CHAOS_TOKEN", "local-demo-token")
    client = TestClient(api.app)
    assert client.post("/chaos", json={"error_rate": 1}).status_code == 401
    headers = {"X-Chaos-Token": "local-demo-token"}
    assert (
        client.post(
            "/chaos",
            headers=headers,
            json={"latency_seconds": 11, "error_rate": 0},
        ).status_code
        == 422
    )
    result = client.post(
        "/chaos",
        headers=headers,
        json={"latency_seconds": 0, "error_rate": 1},
    )
    assert result.status_code == 200
    assert api.chaos_error_rate == 1
    assert client.delete("/chaos", headers=headers).status_code == 200
    assert api.chaos_error_rate == 0


def test_backend_inventory_and_readiness(monkeypatch):
    client = TestClient(backend.app)
    assert client.get("/healthz").status_code == 200
    assert client.get("/inventory/widget").json()["quantity"] == 42
    assert client.get("/readyz").status_code == 200
    monkeypatch.setenv("BACKEND_UNREADY", "1")
    assert client.get("/readyz").status_code == 503
    monkeypatch.setattr(backend, "fail_rate", 1)
    assert client.get("/inventory/widget").status_code == 503
    monkeypatch.setattr(backend, "fail_rate", 0)


def test_mock_jira_create_search_comment_transition():
    mock_jira.issues.clear()
    mock_jira.next_issue = 1
    client = TestClient(mock_jira.app)
    created = client.post(
        "/rest/api/3/issue",
        json={"fields": {"summary": "test", "labels": ["fp-test"]}},
    )
    assert created.json()["key"] == "MOCK-1"
    assert (
        client.get(
            "/rest/api/3/search",
            params={"jql": 'project = "MOCK" AND labels = "fp-test"'},
        ).json()["total"]
        == 1
    )
    assert (
        client.get(
            "/rest/api/3/search/jql",
            params={"jql": 'project = "MOCK" AND labels = "fp-test"'},
        ).json()["total"]
        == 1
    )
    assert (
        client.post("/rest/api/3/issue/MOCK-1/comment", json={"body": "repeat"}).status_code == 200
    )
    assert client.get("/rest/api/3/issue/MOCK-1/transitions").json()["transitions"][0]["id"] == "31"
    assert (
        client.post(
            "/rest/api/3/issue/MOCK-1/transitions",
            json={"transition": {"id": "31"}},
        ).status_code
        == 200
    )


def test_mock_slack_webhook_and_message_list():
    mock_slack.messages.clear()
    client = TestClient(mock_slack.app)
    assert client.post("/webhook", json={"text": "test"}).json()["ok"] is True
    assert client.get("/messages").json()["messages"] == [{"text": "test"}]
