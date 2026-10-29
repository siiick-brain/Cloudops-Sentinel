from __future__ import annotations

import sys

from capture_support import ROOT, read_env

AUTH_DIR = ROOT / "private" / "auth"


def main() -> int:
    env = read_env()
    slack_url = env.get("SLACK_CHANNEL_URL", "").strip()
    jira_url = env.get("JIRA_SITE_URL", "").strip() or env.get("JIRA_BROWSE_URL", "").strip()
    if not slack_url or not jira_url:
        print("Set SLACK_CHANNEL_URL and JIRA_SITE_URL in .env before saving login sessions.")
        return 1
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install the pinned development requirements and Chromium browser first.")
        return 1

    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    print("Warning: private/auth session state is a credential. Delete it when finished.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        for label, url in (("Slack", slack_url), ("Jira", jira_url)):
            page = browser.new_page(
                viewport={"width": 1440, "height": 900},
                color_scheme="dark",
            )
            page.goto(url, wait_until="domcontentloaded")
            input(f"Log in to {label} in the visible browser. Press Enter when finished: ")
            state_path = AUTH_DIR / f"{label.lower()}-storage-state.json"
            page.context.storage_state(path=str(state_path))
            print(f"{label} session state saved under private/auth/.")
            page.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
