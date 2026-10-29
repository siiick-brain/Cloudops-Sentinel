from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import requests
from capture_support import ROOT, CaptureResult, emit, read_env

OUTPUT = ROOT / "docs" / "images" / "demo.gif"
MAX_GIF_BYTES = 5_000_000
VIEWPORT = {"width": 1440, "height": 900}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-running", action="store_true")
    args = parser.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        emit(
            [
                CaptureResult(
                    "demo.gif",
                    "Skipped",
                    "ffmpeg is missing; install it with winget install Gyan.FFmpeg",
                )
            ]
        )
        return
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        emit(
            [
                CaptureResult(
                    "demo.gif",
                    "Skipped",
                    "Install the pinned development requirements and Chromium",
                )
            ]
        )
        return

    env = read_env()
    password = env.get("GRAFANA_ADMIN_PASSWORD", "")
    if not password:
        emit([CaptureResult("demo.gif", "Skipped", "GRAFANA_ADMIN_PASSWORD is not set in .env")])
        return

    configured = env.get("GRAFANA_URL", "").rstrip("/")
    candidates = [configured, "https://localhost", "http://localhost:3000"]
    base = ""
    username = env.get("GRAFANA_ADMIN_USER", "admin")
    api = requests.Session()
    api.verify = False
    api.auth = (username, password)
    dashboards = []
    for candidate in dict.fromkeys(url for url in candidates if url):
        try:
            response = api.get(f"{candidate}/api/search?type=dash-db", timeout=5)
            response.raise_for_status()
            dashboards = response.json()
            base = candidate
            break
        except (requests.RequestException, ValueError):
            continue
    if not base:
        emit([CaptureResult("demo.gif", "Skipped", "Grafana dashboard API is unavailable")])
        return
    slo = next((item for item in dashboards if "slo" in item.get("title", "").casefold()), None)
    if not slo:
        emit([CaptureResult("demo.gif", "Skipped", "Grafana API returned no SLO dashboard")])
        return

    chaos_process = None
    if not args.scenario_running:
        for endpoint in ("http://localhost:8000/readyz", "http://localhost:9090/-/ready"):
            try:
                requests.get(endpoint, timeout=3).raise_for_status()
            except requests.RequestException:
                emit(
                    [
                        CaptureResult(
                            "demo.gif",
                            "Skipped",
                            "Start the development Compose stack before recording the chaos run",
                        )
                    ]
                )
                return
        try:
            requests.get("http://localhost:9093/-/ready", timeout=3).raise_for_status()
        except requests.RequestException:
            emit(
                [
                    CaptureResult(
                        "demo.gif",
                        "Skipped",
                        "Start the development Compose stack before recording the chaos run",
                    )
                ]
            )
            return
        chaos_env = dict(os.environ)
        chaos_env["INTEGRATION_MODE"] = "mock"
        chaos_process = subprocess.Popen(
            [
                sys.executable,
                "chaos/run.py",
                "latency",
                "--duration-seconds",
                "90",
            ],
            cwd=ROOT,
            env=chaos_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    result = CaptureResult("demo.gif", "Failed", "Recording did not complete")
    try:
        result = record_slo_video(sync_playwright, base, slo, username, password, env, ffmpeg)
    except Exception as error:
        result = CaptureResult("demo.gif", "Failed", f"Recording failed: {type(error).__name__}")
    finally:
        if chaos_process is not None:
            try:
                chaos_process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                OUTPUT.unlink(missing_ok=True)
                result = CaptureResult(
                    "demo.gif",
                    "Failed",
                    (
                        "The short latency scenario did not finish within 180 seconds "
                        "and remains running"
                    ),
                )
            else:
                if chaos_process.returncode != 0:
                    OUTPUT.unlink(missing_ok=True)
                    result = CaptureResult(
                        "demo.gif",
                        "Failed",
                        "The latency scenario exited unsuccessfully",
                    )
    emit([result])


def record_slo_video(
    sync_playwright: object,
    base: str,
    slo: dict[str, str],
    username: str,
    password: str,
    env: dict[str, str],
    ffmpeg: str,
) -> CaptureResult:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "private").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="capture-demo-", dir=ROOT / "private") as temporary:
        video_dir = Path(temporary) / "video"
        video_dir.mkdir()
        video_path: Path | None = None
        video_failure = "Playwright did not create a video file"
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            login_context = browser.new_context(ignore_https_errors=True, viewport=VIEWPORT)
            login_page = login_context.new_page()
            try:
                login_page.goto(f"{base}/login", wait_until="domcontentloaded", timeout=15000)
                login_page.locator('input[name="user"]').fill(username)
                login_page.locator('input[name="password"]').fill(password)
                login_page.locator('button[type="submit"]').click()
                login_page.wait_for_url(lambda url: "/login" not in url, timeout=15000)
                state = login_context.storage_state()
            except Exception as error:
                return CaptureResult(
                    "demo.gif",
                    "Failed",
                    f"Grafana authentication failed: {type(error).__name__}",
                )
            finally:
                login_context.close()

            video_context = browser.new_context(
                ignore_https_errors=True,
                viewport=VIEWPORT,
                color_scheme="dark",
                record_video_dir=str(video_dir),
                record_video_size=VIEWPORT,
                storage_state=state,
            )
            page = video_context.new_page()
            dashboard_url = f"{base}{slo['url']}?from=now-1h&to=now&timezone=UTC&theme=dark"
            try:
                page.goto(dashboard_url, wait_until="domcontentloaded", timeout=15000)
                page.wait_for_timeout(12000)
                video_path = page.video.path()
            except Exception as error:
                video_failure = type(error).__name__
            finally:
                video_context.close()
                browser.close()
        if video_path is None or not video_path.is_file():
            emit(
                [
                    CaptureResult(
                        "demo.gif",
                        "Failed",
                        f"Playwright did not record the SLO dashboard: {video_failure}",
                    )
                ]
            )
            return CaptureResult(
                "demo.gif",
                "Failed",
                f"Playwright did not record the SLO dashboard: {video_failure}",
            )

        result = make_gif(ffmpeg, video_path, OUTPUT)
        if result.status == "Captured":
            privacy = save_gif_ocr(OUTPUT, env)
            if privacy.startswith("Found sensitive text"):
                OUTPUT.unlink(missing_ok=True)
                result = CaptureResult("demo.gif", "Failed", privacy)
            elif privacy.startswith("OCR skipped"):
                result = CaptureResult("demo.gif", "Captured", f"12 fps, at most 5 MB; {privacy}")
            else:
                result = CaptureResult(
                    "demo.gif",
                    "Captured",
                    "12 fps, at most 5 MB; OCR found no configured sensitive text",
                )
        return result


def make_gif(ffmpeg: str, video: Path, destination: Path) -> CaptureResult:
    for width in (960, 800, 640, 480):
        command = [
            ffmpeg,
            "-y",
            "-i",
            str(video),
            "-vf",
            (
                f"fps=12,scale={width}:-1:flags=lanczos,split[s0][s1];"
                "[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer"
            ),
            "-loop",
            "0",
            str(destination),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if (
            completed.returncode == 0
            and destination.is_file()
            and destination.stat().st_size <= MAX_GIF_BYTES
        ):
            return CaptureResult("demo.gif", "Captured", f"Rendered at 12 fps and {width}px wide")
    destination.unlink(missing_ok=True)
    return CaptureResult("demo.gif", "Failed", "ffmpeg could not create a GIF smaller than 5 MB")


def save_gif_ocr(path: Path, env: dict[str, str]) -> str:
    from capture_support import scan_png
    from PIL import Image

    with Image.open(path) as gif:
        first_frame = gif.convert("RGB")
        temporary = path.with_suffix(".ocr.png")
        first_frame.save(temporary, format="PNG")
    try:
        return scan_png(temporary, env)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
