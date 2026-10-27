import re
from typing import Any

from fastapi import FastAPI, HTTPException

from app.observability import instrument

app = FastAPI(title="Mock Jira")
issues: dict[str, dict[str, Any]] = {}
next_issue = 1


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/rest/api/3/search")
def search(jql: str = "") -> dict[str, object]:
    matching = [
        {"key": key, "fields": issue["fields"]}
        for key, issue in issues.items()
        if not re.search(r"labels\s*=", jql, re.IGNORECASE)
        or any(label in jql for label in issue.get("labels", []))
    ]
    return {"issues": matching, "total": len(matching)}


@app.post("/rest/api/3/issue")
def create_issue(payload: dict[str, object]) -> dict[str, str]:
    global next_issue
    key = f"MOCK-{next_issue}"
    next_issue += 1
    fields = payload.get("fields", {})
    if not isinstance(fields, dict):
        raise HTTPException(status_code=400, detail="invalid fields")
    issues[key] = {"fields": fields, "labels": fields.get("labels", []), "comments": []}
    return {"key": key, "self": f"/rest/api/3/issue/{key}"}


@app.post("/rest/api/3/issue/{key}/comment")
def comment(key: str, payload: dict[str, object]) -> dict[str, str]:
    if key not in issues:
        raise HTTPException(status_code=404, detail="issue not found")
    comments = issues[key]["comments"]
    if isinstance(comments, list):
        comments.append(payload)
    return {"id": str(len(comments))}


@app.get("/rest/api/3/issue/{key}/transitions")
def transitions(key: str) -> dict[str, object]:
    return {"transitions": [{"id": "31", "name": "Done"}]}


@app.get("/browse/{key}")
def browse_issue(key: str) -> dict[str, object]:
    if key not in issues:
        raise HTTPException(status_code=404, detail="issue not found")
    return {"key": key, **issues[key]}


@app.post("/rest/api/3/issue/{key}/transitions")
def transition(key: str, payload: dict[str, object]) -> dict[str, str]:
    if key not in issues:
        raise HTTPException(status_code=404, detail="issue not found")
    issues[key]["transition"] = payload
    return {"status": "done"}


instrument(app, "mock-jira")
