"""Router behaviour end to end against the in-process Jira and Slack mocks."""

import asyncio

import pytest
import requests
from fastapi.testclient import TestClient

from app import alert_router as router
from app import mock_jira, mock_slack

TOKEN = {"Authorization": "Bearer local-demo-token"}


def group(status="firing", key='{}:{alertname="ApiHighErrorRate"}', alerts=None):
    return {
        "status": status,
        "groupKey": key,
        "commonLabels": {"alertname": "ApiHighErrorRate", "severity": "critical", "service": "api"},
        "commonAnnotations": {
            "summary": "API errors above 5 percent",
            "value": "7.1%",
            "runbook_url": "https://example.test/runbooks/ApiHighErrorRate.md",
            "dashboard_url": "http://localhost:3000/d/golden",
        },
        "alerts": alerts
        or [{"status": status, "fingerprint": "a1"}, {"status": status, "fingerprint": "a2"}],
    }


@pytest.fixture
def mocks(monkeypatch):
    """Route the router's outbound HTTP into the mock apps."""
    jira, slack = TestClient(mock_jira.app), TestClient(mock_slack.app)
    mock_jira.issues.clear()
    mock_jira.next_issue = 1
    mock_slack.messages.clear()
    calls = []

    def fake_request(method, url, auth=None, timeout=None, **kwargs):
        calls.append((method, url))
        return jira.request(method, url.removeprefix("http://jira.test"), **kwargs)

    monkeypatch.setattr(router, "JIRA_MODE", "mock")
    monkeypatch.setattr(router, "_jira_base", "http://jira.test")
    monkeypatch.setattr(router, "_ticket_by_fingerprint", {})
    monkeypatch.setattr(router, "_done_transition_id", None)
    monkeypatch.setattr(router, "_created_at", router.deque())
    monkeypatch.setattr(router, "_last_results", router.deque(maxlen=50))
    monkeypatch.setattr(router.requests, "request", fake_request)
    monkeypatch.setattr(
        router.requests, "post", lambda url, json, timeout: slack.post("/webhook", json=json)
    )
    monkeypatch.setattr(router.time, "sleep", lambda delay: None)
    monkeypatch.setenv("JIRA_PROJECT_KEY", "MOCK")
    monkeypatch.setenv("ROUTER_SHARED_TOKEN", "local-demo-token")
    monkeypatch.setenv("JIRA_MAX_ISSUES_PER_HOUR", "20")
    return calls


def post(payload):
    return TestClient(router.app).post("/webhook", headers=TOKEN, json=payload)


def test_one_ticket_per_group_then_comment_then_done(mocks):
    first = post(group()).json()["results"]
    assert len(first) == 1, "two alerts in one group give one result"
    assert first[0]["issue_key"] == "MOCK-1"
    post(group())
    post(group(status="resolved"))

    assert list(mock_jira.issues) == ["MOCK-1"]
    issue = mock_jira.issues["MOCK-1"]
    assert issue["transition"] == {"transition": {"id": "31"}}
    texts = [c["body"]["content"][0]["content"][0]["text"] for c in issue["comments"]]
    assert texts[0].startswith("Repeated firing alert")
    assert texts[1].startswith("Resolved at ")
    assert (
        "Alerts in group: 2" in issue["fields"]["description"]["content"][0]["content"][0]["text"]
    )


def test_refire_after_done_opens_a_new_ticket(mocks):
    post(group())
    post(group(status="resolved"))
    assert post(group()).json()["results"][0]["issue_key"] == "MOCK-2"


def test_different_groups_get_different_tickets(mocks):
    post(group(key="a"))
    post(group(key="b"))
    assert len(mock_jira.issues) == 2


def test_slack_contract_firing_and_resolved(mocks):
    post(group())
    post(group(status="resolved"))
    firing, resolved = mock_slack.messages
    for message, prefix in ((firing, "[CRITICAL]"), (resolved, "[RESOLVED]")):
        assert message["text"].startswith(prefix)
        section, actions = message["blocks"]
        assert section["type"] == "section" and section["text"]["type"] == "mrkdwn"
        assert "Service: api" in section["text"]["text"]
        assert "Value: 7.1%" in section["text"]["text"]
        buttons = {e["text"]["text"]: e["url"] for e in actions["elements"]}
        assert set(buttons) == {"Dashboard", "Runbook", "Jira ticket"}
        assert buttons["Jira ticket"].endswith("/browse/MOCK-1")


def test_jira_issue_contract(mocks):
    post(group())
    fields = mock_jira.issues["MOCK-1"]["fields"]
    assert fields["summary"] == "[CRITICAL] ApiHighErrorRate"
    assert fields["project"] == {"key": "MOCK"}
    assert fields["description"]["type"] == "doc" and fields["description"]["version"] == 1
    critical, api, fingerprint = fields["labels"]
    assert (critical, api) == ("critical", "api")
    assert fingerprint.startswith("fp-") and len(fingerprint) == 19


def test_rate_limit_caps_creation_and_answers_200(mocks, monkeypatch):
    monkeypatch.setenv("JIRA_MAX_ISSUES_PER_HOUR", "1")
    before = router.REJECTED_TICKETS._value.get()
    assert post(group(key="a")).status_code == 200
    response = post(group(key="b"))
    assert response.status_code == 200, "a 429 here would make Alertmanager retry forever"
    assert response.json()["results"][0]["issue_key"] == ""
    assert len(mock_jira.issues) == 1
    assert len(mock_slack.messages) == 2
    assert router.REJECTED_TICKETS._value.get() == before + 1


def test_rate_limit_window_expires(mocks, monkeypatch):
    monkeypatch.setenv("JIRA_MAX_ISSUES_PER_HOUR", "1")
    router._created_at.append(router.time.time() - 3601)
    assert router._check_rate_limit()


def test_cached_transition_falls_back_when_workflow_differs(mocks, monkeypatch):
    post(group())
    monkeypatch.setattr(router, "_done_transition_id", "999")
    real = router.jira_request

    def reject_stale(method, path, **kwargs):
        if kwargs.get("json") == {"transition": {"id": "999"}}:
            raise requests.HTTPError("400")
        return real(method, path, **kwargs)

    monkeypatch.setattr(router, "jira_request", reject_stale)
    post(group(status="resolved"))
    assert mock_jira.issues["MOCK-1"]["transition"] == {"transition": {"id": "31"}}
    assert router._done_transition_id == "31"


def test_group_alert_falls_back_to_alert_status_and_fingerprint():
    grouped = router.group_alert({"alerts": [{"status": "resolved", "fingerprint": "z"}]})
    assert grouped["status"] == "resolved"
    assert grouped["count"] == 1
    assert (
        grouped["fingerprint"]
        == router.group_alert({"alerts": [{"fingerprint": "z"}]})["fingerprint"]
    )


def test_empty_webhook_and_latest(mocks):
    client = TestClient(router.app)
    assert post({"alerts": []}).json() == {"results": []}
    assert client.get("/latest").status_code == 401
    assert client.get("/latest", headers=TOKEN).json() == {"results": []}
    assert client.get("/healthz").json() == {"status": "ok", "mode": "mock"}


def test_slack_rejection_and_network_failures(monkeypatch):
    class Response:
        status_code = 404
        text = "no_service"

    monkeypatch.setattr(router.time, "sleep", lambda delay: None)
    monkeypatch.setattr(router.requests, "post", lambda *a, **k: Response())
    with pytest.raises(RuntimeError, match="rejected"):
        router._post_slack({"text": "x"})

    def boom(*a, **k):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(router.requests, "post", boom)
    with pytest.raises(RuntimeError, match="after retries"):
        router._post_slack({"text": "x"})


def test_slack_stays_rate_limited(monkeypatch):
    class Limited:
        status_code = 429
        headers = {"Retry-After": "not-a-number"}

    delays = []
    monkeypatch.setattr(router.time, "sleep", delays.append)
    monkeypatch.setattr(router.requests, "post", lambda *a, **k: Limited())
    with pytest.raises(RuntimeError, match="rate limited"):
        router._post_slack({"text": "x"})
    assert delays == [1, 1]


def test_slack_plain_ok_records_acceptance_time(monkeypatch):
    class Ok:
        status_code = 200

        def json(self):
            raise requests.JSONDecodeError("x", "ok", 0)

    monkeypatch.setattr(router.requests, "post", lambda *a, **k: Ok())
    assert router._post_slack({"text": "x"}).startswith("accepted ")


def test_jira_network_failure_exhausts_retries(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("down")

    sleeps = []
    monkeypatch.setattr(router.requests, "request", boom)
    monkeypatch.setattr(router.time, "sleep", sleeps.append)
    with pytest.raises(RuntimeError, match="after retries"):
        router.jira_request("GET", "/x")
    assert sleeps == [1, 2, 4], "exponential backoff between attempts"


def test_jira_server_error_exhausts_retries(monkeypatch):
    class Failing:
        status_code = 503

        def raise_for_status(self):
            raise requests.HTTPError("503")

    monkeypatch.setattr(router.requests, "request", lambda *a, **k: Failing())
    monkeypatch.setattr(router.time, "sleep", lambda delay: None)
    with pytest.raises(requests.HTTPError):
        router.jira_request("GET", "/x")


def test_missing_done_transition_is_an_error(monkeypatch):
    class Body:
        def json(self):
            return {"transitions": [{"id": "1", "name": "In Progress"}]}

    monkeypatch.setattr(router, "jira_request", lambda *a, **k: Body())
    with pytest.raises(RuntimeError, match="no Done transition"):
        router.fetch_done_transition("MOCK-1")


def test_configuration_modes(monkeypatch):
    monkeypatch.setattr(router, "JIRA_MODE", "staging")
    with pytest.raises(RuntimeError, match="mock or real"):
        router.validate_configuration()

    monkeypatch.setattr(router, "JIRA_MODE", "real")
    monkeypatch.delenv("ROUTER_SHARED_TOKEN", raising=False)
    for key, value in {
        "JIRA_BASE_URL": "https://example.atlassian.net/",
        "JIRA_EMAIL": "ops@example.test",
        "JIRA_API_TOKEN": "t",
        "JIRA_PROJECT_KEY": "OPS",
        "SLACK_WEBHOOK_URL": "https://hooks.example.test/x",
    }.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError, match="ROUTER_SHARED_TOKEN"):
        router.validate_configuration()

    monkeypatch.setenv("ROUTER_SHARED_TOKEN", "s")
    monkeypatch.setattr(router, "_jira_base", "")
    router.validate_configuration()
    assert router._jira_base == "https://example.atlassian.net"
    assert router._jira_auth == ("ops@example.test", "t")


def test_real_mode_startup_caches_done_transition(monkeypatch):
    monkeypatch.setattr(router, "JIRA_MODE", "real")
    monkeypatch.setattr(router, "validate_configuration", lambda: None)
    monkeypatch.setattr(router, "_done_transition_id", None)
    monkeypatch.setenv("JIRA_PROJECT_KEY", "OPS")

    class Body:
        def __init__(self, data):
            self.data = data

        def json(self):
            return self.data

    def fake(method, path, **kwargs):
        if path.endswith("/transitions"):
            return Body({"transitions": [{"id": "41", "name": "Done"}]})
        return Body({"issues": [{"key": "OPS-7"}]})

    monkeypatch.setattr(router, "jira_request", fake)

    async def start():
        async with router.lifespan(router.app):
            pass

    asyncio.run(start())
    assert router._done_transition_id == "41"


def test_mock_ticket_url_ignores_real_browse_url(mocks, monkeypatch):
    monkeypatch.setenv("JIRA_BROWSE_URL", "https://example.atlassian.net/browse")
    url = post(group()).json()["results"][0]["ticket_url"]
    assert url == "http://localhost:8092/browse/MOCK-1"


def test_real_ticket_url_has_single_browse(mocks, monkeypatch):
    monkeypatch.setattr(router, "JIRA_MODE", "real")
    monkeypatch.setenv("JIRA_BROWSE_URL", "https://example.atlassian.net/browse/")
    url = post(group()).json()["results"][0]["ticket_url"]
    assert url == "https://example.atlassian.net/browse/MOCK-1"
