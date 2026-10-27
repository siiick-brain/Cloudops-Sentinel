from fastapi import FastAPI, Request

from app.observability import instrument

app = FastAPI(title="Mock Slack")
messages: list[dict[str, object]] = []


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook")
async def receive(request: Request) -> dict[str, object]:
    payload = await request.json()
    messages.append(payload)
    return {"ok": True, "ts": str(len(messages))}


@app.get("/messages")
def get_messages() -> dict[str, object]:
    return {"messages": messages}


instrument(app, "mock-slack")
