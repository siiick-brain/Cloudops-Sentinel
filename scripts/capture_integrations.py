from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path

from capture_support import (
    ROOT,
    CaptureResult,
    blur_private_page,
    emit,
    read_env,
    save_png,
)
from PIL import Image

AUTH_DIR = ROOT / "private" / "auth"
VIEWPORT = {"width": 1440, "height": 900}


def skip(name: str, reason: str) -> CaptureResult:
    return CaptureResult(name, "Skipped", reason)


def ticket_url() -> str | None:
    text = (ROOT / "docs" / "live-verification.md").read_text(encoding="utf-8")
    match = re.search(r"https?://[^\s)>\]]+/browse/[A-Z][A-Z0-9]+-\d+", text)
    return match.group(0).rstrip(".,") if match else None


def capture_page(
    browser: object, url: str, state: Path, name: str, env: dict[str, str]
) -> CaptureResult:
    context = browser.new_context(
        storage_state=str(state),
        ignore_https_errors=True,
        viewport=VIEWPORT,
        color_scheme="dark",
    )
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1500)
        if (
            "/login" in page.url.casefold()
            or "sign in" in (page.title() + page.locator("body").inner_text()).casefold()
        ):
            return skip(name, "Saved login state has expired; run scripts/save_login.py")
        blur_private_page(page, env)
        text = page.locator("body").inner_text(timeout=5000).casefold()
        if name == "slack-alert.png" and not any(
            word in text for word in ("firing", "apihigh", "targetdown")
        ):
            return skip(name, "No firing alert message is visible in the configured Slack channel")
        if name == "slack-resolved.png" and "resolved" not in text:
            return skip(
                name, "No resolved alert message is visible in the configured Slack channel"
            )
        if name == "jira-resolved.png" and "done" not in text:
            return skip(name, "The Jira issue does not show a Done state")
        return save_png(Image.open(BytesIO(page.screenshot(full_page=False))), name, env)
    except Exception as error:
        return CaptureResult(
            name,
            "Failed",
            f"Integration capture failed: {type(error).__name__}",
        )
    finally:
        context.close()


def main() -> None:
    names = ["slack-alert.png", "slack-resolved.png", "jira-ticket.png", "jira-resolved.png"]
    env = read_env()
    slack_url = env.get("SLACK_CHANNEL_URL", "").strip()
    issue = ticket_url()
    states = {
        "slack": AUTH_DIR / "slack-storage-state.json",
        "jira": AUTH_DIR / "jira-storage-state.json",
    }
    results: list[CaptureResult] = []
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        emit(
            [
                skip(name, "Install the pinned development requirements and Chromium browser")
                for name in names
            ]
        )
        return

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        if not slack_url:
            results.extend(
                [
                    skip(name, "Set SLACK_CHANNEL_URL in .env and run scripts/save_login.py")
                    for name in names[:2]
                ]
            )
        elif not states["slack"].is_file():
            results.extend(
                [
                    skip(name, "Run scripts/save_login.py to create the private Slack session")
                    for name in names[:2]
                ]
            )
        else:
            results.extend(
                capture_page(browser, slack_url, states["slack"], name, env) for name in names[:2]
            )

        if not issue:
            reason = "No Jira ticket URL is recorded in docs/live-verification.md"
            results.extend([skip(name, reason) for name in names[2:]])
        elif not states["jira"].is_file():
            results.extend(
                [
                    skip(name, "Run scripts/save_login.py to create the private Jira session")
                    for name in names[2:]
                ]
            )
        else:
            results.append(capture_page(browser, issue, states["jira"], names[2], env))
            results.append(capture_page(browser, issue, states["jira"], names[3], env))
        browser.close()
    emit(results)


if __name__ == "__main__":
    main()
