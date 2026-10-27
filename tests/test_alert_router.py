import pytest
import requests
from fastapi.testclient import TestClient

from app import alert_router as router


@pytest.fixture(autouse=True)
def isolate_router(monkeypatch):
    monkeypatch.setattr(router, "JIRA_MODE", "mock")
    monkeypatch.setattr(router, "_ticket_by_fingerprint", {})
    monkeypatch.setattr(router, "_transitions", {})
    monkeypatch.setattr(router, "_created_at", router.deque())
    monkeypatch.setenv("JIRA_PROJECT_KEY", "MOCK")
    monkeypatch.setenv("ROUTER_SHARED_TOKEN", "local-demo-token")
    monkeypatch.setenv("JIRA_MAX_ISSUES_PER_HOUR", "20")


def test_firing_repeat_and_resolve_flow(monkeypatch):
    tickets = {}
    comments = []
    slack = []
    issue_payloads = []
    monkeypatch.setattr(router, "_jira_base", "http://jira.test")
    monkeypatch.setattr(router, "_slack_url", "http://slack.test")

    def fake_jira(method, path, **kwargs):
        if path == "/rest/api/3/search/jql":
            label = kwargs["params"]["jql"].split('"')[-2]
            return FakeResponse(
                {"issues": [{"key": tickets[label]}]} if label in tickets else {"issues": []}
            )
        if path == "/rest/api/3/issue":
            issue_payloads.append(kwargs["json"])
            labels = kwargs["json"]["fields"]["labels"]
            key = "MOCK-1"
            tickets[labels[-1]] = key
            return FakeResponse({"key": key})
        if path.endswith("/transitions") and method == "GET":
            return FakeResponse({"transitions": [{"id": "77", "name": "Done"}]})
        if path.endswith("/comment"):
            comments.append(kwargs["json"])
            return FakeResponse({"id": "1"})
        if path.endswith("/transitions") and method == "POST":
            return FakeResponse({})
        raise AssertionError((method, path))

    monkeypatch.setattr(router, "jira_request", fake_jira)
    monkeypatch.setattr(router, "_post_slack", lambda payload: slack.append(payload) or "ts-1")
    alert = {
        "fingerprint": "abcdef",
        "status": "firing",
        "labels": {"alertname": "ApiHighErrorRate", "severity": "critical", "service": "api"},
        "annotations": {
            "summary": "API errors",
            "description": "error rate is high",
            "dashboard_url": "https://grafana.example/d",
            "runbook_url": "https://docs.example/runbook",
        },
    }
    created = router.process_alert(alert)
    assert created["issue_key"] == "MOCK-1"
    assert router.process_alert(alert)["issue_key"] == "MOCK-1"
    resolved = {**alert, "status": "resolved"}
    router.process_alert(resolved)
    assert len(tickets) == 1
    fields = issue_payloads[0]["fields"]
    assert fields["issuetype"] == {"name": "Task"}
    assert fields["description"]["type"] == "doc"
    assert {"critical", "api", "fp-abcdef"} == set(fields["labels"])
    assert "https://grafana.example/d" in fields["description"]["content"][0]["content"][0]["text"]
    assert len(comments) == 2
    assert len(slack) == 3
    assert slack[0]["blocks"][0]["text"]["text"].startswith("*[CRITICAL]")
    assert "Jira ticket" in [action["text"]["text"] for action in slack[0]["blocks"][1]["elements"]]
    assert slack[-1]["text"].startswith("[RESOLVED]")
    assert len(slack[0]["blocks"][1]["elements"]) == 3


def test_rate_limit_is_counted(monkeypatch):
    monkeypatch.setenv("JIRA_MAX_ISSUES_PER_HOUR", "0")
    monkeypatch.setattr(router, "_search_ticket", lambda fingerprint: None)
    before = router.REJECTED_TICKETS._value.get()
    with pytest.raises(router.HTTPException) as error:
        router.process_alert(
            {
                "fingerprint": "limited",
                "labels": {"alertname": "RateLimit", "service": "api"},
                "annotations": {},
            }
        )
    assert error.value.status_code == 429
    assert router.REJECTED_TICKETS._value.get() == before + 1


def test_jira_transient_retry(monkeypatch):
    attempts = []
    responses = [FakeResponse({}, status_code=503), FakeResponse({"ok": True})]
    monkeypatch.setattr(
        router.requests, "request", lambda *args, **kwargs: attempts.append(1) or responses.pop(0)
    )
    monkeypatch.setattr(router.time, "sleep", lambda delay: None)
    assert router.jira_request("GET", "/retry").json() == {"ok": True}
    assert len(attempts) == 2


def test_jira_client_error_is_not_retried(monkeypatch):
    attempts = []
    response = FakeResponse({}, status_code=400)
    monkeypatch.setattr(
        router.requests,
        "request",
        lambda *args, **kwargs: attempts.append(1) or response,
    )
    with pytest.raises(requests.HTTPError):
        router.jira_request("POST", "/bad-request")
    assert len(attempts) == 1


def test_slack_retries_rate_limit(monkeypatch):
    class SlackResponse:
        def __init__(self, status, headers=None):
            self.status_code = status
            self.headers = headers or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError(str(self.status_code))

        def json(self):
            return {"ok": True}

    responses = [SlackResponse(429, {"Retry-After": "0"}), SlackResponse(200)]
    calls = []
    monkeypatch.setattr(
        router.requests, "post", lambda *args, **kwargs: calls.append(1) or responses.pop(0)
    )
    monkeypatch.setattr(router.time, "sleep", lambda delay: None)
    router._post_slack({"text": "test"})
    assert len(calls) == 2


def test_real_mode_names_missing_configuration(monkeypatch):
    monkeypatch.setattr(router, "JIRA_MODE", "real")
    for key in (
        "JIRA_BASE_URL",
        "JIRA_EMAIL",
        "JIRA_API_TOKEN",
        "JIRA_PROJECT_KEY",
        "SLACK_WEBHOOK_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="JIRA_BASE_URL"):
        router.validate_configuration()


def test_webhook_rejects_bad_token_and_processes_alert(monkeypatch):
    monkeypatch.setattr(router, "process_alert", lambda alert: {"issue_key": "MOCK-1"})
    client = TestClient(router.app)
    payload = {"alerts": [{"fingerprint": "x"}]}
    assert client.post("/webhook", json=payload).status_code == 401
    response = client.post(
        "/webhook",
        headers={"Authorization": "Bearer local-demo-token"},
        json=payload,
    )
    assert response.json() == {"results": [{"issue_key": "MOCK-1"}]}


class FakeResponse:
    def __init__(self, body, status_code=200):
        self.body = body
        self.status_code = status_code

    def json(self):
        return self.body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code), response=self)
