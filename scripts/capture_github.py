from __future__ import annotations

import json
import subprocess
from io import BytesIO
from pathlib import Path

from capture_support import CaptureResult, emit, read_env, save_png
from PIL import Image

VIEWPORT = {"width": 1440, "height": 900}
NAMES = [
    "github-repo.png",
    "github-actions.png",
    "github-runbook.png",
    "github-contributors.png",
]


def skip_all(reason: str) -> list[CaptureResult]:
    return [CaptureResult(name, "Skipped", reason) for name in NAMES]


def main() -> None:
    try:
        completed = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner,isPrivate,defaultBranchRef"],
            cwd=Path(__file__).resolve().parents[1],
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        repository = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        emit(skip_all("gh repo view could not identify a GitHub repository"))
        return
    if repository.get("isPrivate") is not False:
        emit(skip_all("The repository is not public"))
        return
    name = repository.get("nameWithOwner")
    branch = (repository.get("defaultBranchRef") or {}).get("name") or "main"
    if not name:
        emit(skip_all("gh repo view did not return a repository name"))
        return
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        emit(skip_all("Install the pinned development requirements and Chromium browser"))
        return

    urls = [
        f"https://github.com/{name}",
        f"https://github.com/{name}/actions",
        f"https://github.com/{name}/blob/{branch}/docs/runbooks/ApiHighLatency.md",
        f"https://github.com/{name}/graphs/contributors",
    ]
    env = read_env()
    results: list[CaptureResult] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, color_scheme="dark")
        for filename, url in zip(NAMES, urls, strict=True):
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(1000)
                if page.locator("body").inner_text().strip() == "Not Found":
                    results.append(
                        CaptureResult(filename, "Skipped", "GitHub page is not available")
                    )
                    continue
                screenshot = Image.open(BytesIO(page.screenshot(full_page=False)))
                results.append(save_png(screenshot, filename, env))
            except Exception:
                results.append(
                    CaptureResult(filename, "Skipped", "Public GitHub page did not load")
                )
        browser.close()
    emit(results)


if __name__ == "__main__":
    main()
