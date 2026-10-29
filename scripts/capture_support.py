from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "docs" / "images"
MAX_PNG_BYTES = 500 * 1024
PRESERVED_SCREENSHOTS = frozenset(
    {
        "P2-16-deployment-verification.png",
        "grafana-distributed-traces.png",
        "grafana-golden-signals.png",
        "grafana-node-container-health.png",
        "grafana-slo-error-budget.png",
        "prometheus-alert-rules.png",
        "prometheus-container-cpu-metrics.png",
        "prometheus-cpu-alert-firing.png",
        "prometheus-targets-up.png",
    }
)


@dataclass(frozen=True)
class CaptureResult:
    image: str
    status: str
    reason: str


def read_env() -> dict[str, str]:
    values = dict(os.environ)
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return values
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip("\"'")
        if value:
            values.setdefault(key.strip(), value)
    return values


def emit(results: list[CaptureResult]) -> None:
    for result in results:
        print(json.dumps(asdict(result), ensure_ascii=True))


def image_path(name: str) -> Path:
    return IMAGE_DIR / name


def save_png(image: Image.Image, name: str, env: dict[str, str]) -> CaptureResult:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    destination = image_path(name)
    if name in PRESERVED_SCREENSHOTS and destination.is_file():
        return CaptureResult(
            name,
            "Skipped",
            "Preserved the selected existing screenshot instead of replacing it",
        )
    image.save(destination, format="PNG", optimize=True)
    if destination.stat().st_size > MAX_PNG_BYTES:
        image.convert("P", palette=Image.Palette.ADAPTIVE, colors=256).save(
            destination,
            format="PNG",
            optimize=True,
        )
    if destination.stat().st_size > MAX_PNG_BYTES:
        destination.unlink(missing_ok=True)
        return CaptureResult(name, "Failed", "PNG exceeds the 500 KB limit after optimization")
    privacy = scan_png(destination, env)
    if privacy.startswith("Found sensitive text"):
        destination.unlink(missing_ok=True)
        return CaptureResult(name, "Failed", privacy)
    if privacy.startswith("OCR skipped"):
        return CaptureResult(name, "Captured", f"PNG optimized; {privacy}")
    return CaptureResult(name, "Captured", "PNG optimized; OCR found no configured sensitive text")


def sensitive_values(env: dict[str, str]) -> tuple[list[str], list[str]]:
    emails: set[str] = set()
    hosts: set[str] = set()
    for key in ("JIRA_EMAIL", "SLACK_EMAIL"):
        value = env.get(key, "").strip()
        if "@" in value:
            emails.add(value.lower())
    workspace_names = [
        env.get("SLACK_WORKSPACE_NAME", "").strip(),
        env.get("JIRA_WORKSPACE_NAME", "").strip(),
    ]
    for key in (
        "SLACK_CHANNEL_URL",
        "SLACK_WEBHOOK_URL",
        "JIRA_SITE_URL",
        "JIRA_BASE_URL",
        "JIRA_BROWSE_URL",
    ):
        value = env.get(key, "").strip()
        if not value:
            continue
        host = urlparse(value if "://" in value else f"https://{value}").hostname
        if host and host not in {"localhost", "127.0.0.1"}:
            hosts.add(host.lower())
    verification_file = ROOT / "docs" / "live-verification.md"
    if verification_file.is_file():
        match = re.search(
            r"https?://[^\s)>\]]+/browse/[A-Z][A-Z0-9]+-\d+",
            verification_file.read_text(encoding="utf-8"),
        )
        if match:
            host = urlparse(match.group(0)).hostname
            if host:
                hosts.add(host.lower())
    return sorted(emails), sorted(hosts + [name.lower() for name in workspace_names if name])


def scan_png(path: Path, env: dict[str, str]) -> str:
    try:
        import pytesseract
    except ImportError:
        return "OCR skipped because pytesseract is not installed"
    if not shutil.which("tesseract"):
        return "OCR skipped because the Tesseract executable is not installed"
    try:
        text = pytesseract.image_to_string(Image.open(path)).lower()
    except (
        OSError,
        RuntimeError,
        pytesseract.TesseractError,
        pytesseract.TesseractNotFoundError,
    ):
        return "OCR skipped because the local OCR engine could not read the PNG"
    emails, hosts = sensitive_values(env)
    if any(value in text for value in emails + hosts):
        return "Found sensitive text matching a configured email or service host"
    if re.search(
        r"\b(?:xox[baprsoc]-[a-z0-9-]{10,}|xapp-[a-z0-9-]{10,}|gh[pousr]_[a-z0-9]{20,}|"
        r"atatt3x[a-z0-9_=-]{12,}|eyj[a-z0-9_-]{10,}\.[a-z0-9_-]{10,}|"
        r"bearer\s+[a-z0-9._~+/-]{16,}|token[=:]\s*[a-z0-9._~+/-]{16,})\b",
        text,
    ):
        return "Found token-like text"
    return "OCR passed"


def blur_private_page(page: object, env: dict[str, str]) -> None:
    emails, hosts = sensitive_values(env)
    page.add_style_tag(
        content="""
        header, [role="banner"], [data-qa*="current_user"],
        [data-qa*="workspace"], [data-testid*="avatar"],
        [data-qa*="avatar"], [class*="avatar"], [aria-label*="profile" i],
        [data-qa="team-menu"], [data-qa="workspace-switcher"],
        [data-testid="atlassian-navigation--header"] {
          filter: blur(12px) !important;
        }
        .capture-sensitive { filter: blur(12px) !important; }
        """
    )
    page.evaluate(
        r"""({emails, hosts}) => {
          const patterns = [
            /(?:xox[baprsoc]-[a-z0-9-]{10,}|xapp-[a-z0-9-]{10,}|gh[pousr]_[a-z0-9]{20,}|atatt3x[a-z0-9_=-]{12,}|eyj[a-z0-9_-]{10,}\.[a-z0-9_-]{10,}|bearer\s+[a-z0-9._~+/-]{16,}|token[=:]\s*[a-z0-9._~+/-]{16,})/i
          ];
          const values = [...emails, ...hosts].map(value => value.toLowerCase());
          for (const element of document.querySelectorAll("body *")) {
            const text = (element.innerText || "").trim();
            if (!text || text.length > 300) continue;
            const lower = text.toLowerCase();
            if (values.some(value => lower.includes(value)) ||
                patterns.some(pattern => pattern.test(text))) {
              element.classList.add("capture-sensitive");
            }
          }
        }""",
        {"emails": emails, "hosts": hosts},
    )
