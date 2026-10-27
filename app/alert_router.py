import json
import logging
import os
import re
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter

from app.observability import instrument

logger = logging.getLogger("alert_router")
REJECTED_TICKETS = Counter(
    "jira_ticket_creation_rejected_total",
    "Jira ticket creations rejected by the hourly rate limit",
)
JIRA_MODE = os.getenv("INTEGRATION_MODE", "mock")
_created_at: deque[float] = deque()
_ticket_by_fingerprint: dict[str, str] = {}
_last_results: list[dict[str, str | None]] = []
_jira_base = os.getenv("JIRA_BASE_URL", "http://mock-jira:8080")
_slack_url = os.getenv("SLACK_WEBHOOK_URL", "http://mock-slack:8080/webhook")
_jira_auth: tuple[str, str] | None = None
_transitions: dict[str, str] = {}



@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    validate_configuration()
    if JIRA_MODE == "real":
        jira_request("GET", "/rest/api/3/project/" + os.environ["JIRA_PROJECT_KEY"])
        project_key = os.environ["JIRA_PROJECT_KEY"]
        existing = (
            jira_request(
                "GET",
                "/rest/api/3/search/jql",
                params={
                    "jql": f'project = "{project_key}" AND statusCategory != Done',
                    "maxResults": 1,
                },
            )
            .json()
            .get("issues", [])
        )
        if existing:
            issue_key = str(existing[0].get("key", ""))
            if issue_key:
                _transitions[issue_key] = fetch_done_transition(issue_key)
    yield



app = FastAPI(title="CloudOps Sentinel alert router", lifespan=lifespan)


def validate_configuration() -> None:
    if JIRA_MODE not in {"mock", "real"}:
        raise RuntimeError("INTEGRATION_MODE must be mock or real")
    if JIRA_MODE == "real":
        required = (
            "JIRA_BASE_URL",
            "JIRA_EMAIL",
            "JIRA_API_TOKEN",
            "JIRA_PROJECT_KEY",
            "SLACK_WEBHOOK_URL",
        )
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise RuntimeError(f"Real integrations require: {', '.join(missing)}")
        global _jira_auth, _jira_base, _slack_url
        _jira_base = os.environ["JIRA_BASE_URL"].rstrip("/")
        _jira_auth = (os.environ["JIRA_EMAIL"], os.environ["JIRA_API_TOKEN"])
        _slack_url = os.environ["SLACK_WEBHOOK_URL"]


def jira_request(method: str, path: str, **kwargs: Any) -> requests.Response:
    for attempt in range(4):
        try:
            response = requests.request(
                method,
                f"{_jira_base}{path}",
                auth=_jira_auth,
                timeout=10,
                **kwargs,
            )
        except requests.RequestException as exc:
            if attempt == 3:
                logger.error(
                    json.dumps(
                        {
                            "event": "jira_request_failed",
                            "path": path,
                            "attempt": attempt + 1,
                            "error_type": type(exc).__name__,
                        }
                    )
                )
                raise RuntimeError("Jira request failed after retries") from None
            logger.warning(
                json.dumps(
                    {
                        "event": "jira_request_retry",
                        "path": path,
                        "attempt": attempt + 1,
                    }
                )
            )
            time.sleep(min(2**attempt, 8))
            continue
        if response.status_code != 429 and response.status_code < 500:
            response.raise_for_status()
            logger.info(
                json.dumps({"event": "jira_request", "path": path, "status": response.status_code})
            )
            return response
        if attempt == 3:
            response.raise_for_status()
        else:
            logger.warning(
                json.dumps(
                    {
                        "event": "jira_request_retry",
                        "path": path,
                        "attempt": attempt + 1,
                        "status": response.status_code,
                    }
                )
            )
        time.sleep(min(2**attempt, 8))
    raise RuntimeError("Jira request retry loop ended unexpectedly")


def fetch_done_transition(issue_key: str) -> str:
    transitions = jira_request("GET", f"/rest/api/3/issue/{issue_key}/transitions").json()[
        "transitions"
    ]
    for transition in transitions:
        if transition.get("name", "").lower() == "done":
            return str(transition["id"])
    raise RuntimeError("Jira issue has no Done transition")


def _safe_label(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "-", value)[:80]


def _adf(text: str) -> dict[str, object]:
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


def _search_ticket(fingerprint_label: str) -> str | None:
    if fingerprint_label in _ticket_by_fingerprint:
        return _ticket_by_fingerprint[fingerprint_label]
    project = os.getenv("JIRA_PROJECT_KEY", "MOCK")
    jql = f'project = "{project}" AND labels = "{fingerprint_label}"'
    
    result = jira_request(
        "GET",
        "/rest/api/3/search/jql",
        params={"jql": jql, "fields": "summary,labels"},
    ).json()

    issues = result.get("issues", [])
    return str(issues[0]["key"]) if issues else None


def _check_rate_limit() -> bool:
    now = time.time()
    while _created_at and _created_at[0] <= now - 3600:
        _created_at.popleft()
    limit = int(os.getenv("JIRA_MAX_ISSUES_PER_HOUR", "20"))
    if len(_created_at) >= limit:
        return False
    _created_at.append(now)
    return True


def _post_slack(payload: dict[str, object]) -> str | None:
    for attempt in range(3):
        try:
            response = requests.post(_slack_url, json=payload, timeout=10)
        except requests.RequestException as exc:
            logger.warning(
                json.dumps(
                    {
                        "event": "slack_request_retry",
                        "attempt": attempt + 1,
                        "error_type": type(exc).__name__,
                    }
                )
            )
            if attempt == 2:
                logger.error(json.dumps({"event": "slack_request_failed", "attempt": attempt + 1}))
                raise RuntimeError("Slack webhook request failed after retries") from None
            time.sleep(min(2**attempt, 8))
            continue
        if response.status_code != 429:
            
            if response.status_code >= 400:
                logger.error(
                    json.dumps(
                        {
                            "event": "slack_request_failed",
                            "status": response.status_code,
                            "response_body": response.text[:500],
                        }
                    )
                )
                raise RuntimeError("Slack webhook rejected the message")

            logger.info(
                json.dumps({"event": "slack_message_accepted", "status": response.status_code})
            )
            try:
                body = response.json()
            except requests.JSONDecodeError:
                return None
            timestamp = body.get("ts")
            return str(timestamp) if timestamp is not None else None
        try:
            delay = min(max(float(response.headers.get("Retry-After", "1")), 0), 30)
        except ValueError:
            delay = 1
        logger.warning(
            json.dumps(
                {
                    "event": "slack_rate_limited",
                    "attempt": attempt + 1,
                    "retry_after": delay,
                }
            )
        )
        if attempt < 2:
            time.sleep(delay)
    raise RuntimeError("Slack webhook remained rate limited after retries")


def process_alert(alert: dict[str, Any]) -> dict[str, str | None]:
    labels = alert.get("labels", {})
    annotations = alert.get("annotations", {})
    fingerprint = str(alert.get("fingerprint", "unknown"))
    fingerprint_label = f"fp-{_safe_label(fingerprint)}"
    status = str(alert.get("status", "firing"))
    name = str(labels.get("alertname", "UnknownAlert"))
    severity = str(labels.get("severity", "warning"))
    service = str(labels.get("service", "unknown"))
    summary = str(annotations.get("summary", name))
    dashboard = str(
        annotations.get("dashboard_url", os.getenv("GRAFANA_URL", "http://localhost:3000"))
    )
    runbook = str(annotations.get("runbook_url", ""))
    issue_key = _search_ticket(fingerprint_label)
    if status == "resolved":
        if issue_key:
            jira_request(
                "POST",
                f"/rest/api/3/issue/{issue_key}/comment",
                json={
                    "body": _adf(
                        f"Resolved at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}."
                    )
                },
            )
            transition_id = _transitions.get(issue_key) or fetch_done_transition(issue_key)
            jira_request(
                "POST",
                f"/rest/api/3/issue/{issue_key}/transitions",
                json={"transition": {"id": transition_id}},
            )
    elif issue_key:
        jira_request(
            "POST",
            f"/rest/api/3/issue/{issue_key}/comment",
            json={"body": _adf(f"Repeated firing alert: {summary}")},
        )
    else:
        if not _check_rate_limit():
            REJECTED_TICKETS.inc()
            logger.warning(json.dumps({"event": "ticket_rate_limited", "fingerprint": fingerprint}))
            raise HTTPException(status_code=429, detail="Jira issue creation rate limit reached")
        project = os.getenv("JIRA_PROJECT_KEY", "MOCK")
        issue = jira_request(
            "POST",
            "/rest/api/3/issue",
            json={
                "fields": {
                    "project": {"key": project},
                    "issuetype": {"name": "Task"},
                    "summary": f"[{severity.upper()}] {name}",
                    "description": _adf(f"{summary}\nDashboard: {dashboard}\nRunbook: {runbook}"),
                    "labels": [_safe_label(severity), _safe_label(service), fingerprint_label],
                }
            },
        ).json()
        issue_key = str(issue["key"])
        _ticket_by_fingerprint[fingerprint_label] = issue_key
        _transitions[issue_key] = fetch_done_transition(issue_key)

    browse_base = os.getenv("JIRA_BROWSE_URL") or (
        _jira_base if JIRA_MODE == "real" else "http://localhost:8092"
    )
    ticket_url = f"{browse_base.rstrip('/')}/browse/{issue_key}" if issue_key else ""
    status_text = "RESOLVED" if status == "resolved" else severity.upper()
    value = str(annotations.get("value", annotations.get("description", "")))
    text = f"[{status_text}] {summary}"
    actions = [
        {"type": "button", "text": {"type": "plain_text", "text": "Dashboard"}, "url": dashboard},
        {"type": "button", "text": {"type": "plain_text", "text": "Runbook"}, "url": runbook},
    ]
    if ticket_url:
        actions.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Jira ticket"},
                "url": ticket_url,
            }
        )
    slack_timestamp = _post_slack(
        {
            "text": text,
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{text}*\nService: {service}\nValue: {value}",
                    },
                },
                {"type": "actions", "elements": actions},
            ],
        }
    )
    logger.info(
        json.dumps(
            {
                "event": "alert_processed",
                "status": status,
                "fingerprint": fingerprint,
                "issue_key": issue_key,
            }
        )
    )
    return {
        "issue_key": issue_key or "",
        "ticket_url": ticket_url,
        "slack_timestamp": slack_timestamp,
        "alertname": name,
        "status": status,
    }


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
async def webhook(request: Request) -> dict[str, object]:
    token = os.getenv("ROUTER_SHARED_TOKEN", "local-demo-token")
    if request.headers.get("Authorization") != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="invalid router token")
    payload = await request.json()
    results: list[dict[str, str | None]] = []
    for alert in payload.get("alerts", []):
        results.append(process_alert(alert))
    _last_results[:] = results
    return {"results": results}


@app.get("/latest")
def latest(request: Request) -> dict[str, object]:
    token = os.getenv("ROUTER_SHARED_TOKEN", "local-demo-token")
    if request.headers.get("Authorization") != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="invalid router token")
    return {"results": _last_results}


def _process_group(alerts: list[dict[str, Any]]) -> list[dict[str, str | None]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for alert in alerts:
        grouped[str(alert.get("fingerprint", "unknown"))].append(alert)
    return [process_alert(group[0]) for group in grouped.values()]


instrument(app, "alert-router")

