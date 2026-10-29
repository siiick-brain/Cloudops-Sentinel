from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

if __package__:
    from .capture_support import ROOT, read_env, save_png
else:
    from capture_support import ROOT, read_env, save_png
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\consola.ttf"),
    Path(r"C:\Windows\Fonts\lucon.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    raise FileNotFoundError("No supported monospace font is installed for terminal rendering")


def wrap_exact(text: str, max_characters: int) -> list[str]:
    lines: list[str] = []
    for original in text.split("\n"):
        if not original:
            lines.append("")
            continue
        lines.extend(
            original[index : index + max_characters]
            for index in range(0, len(original), max_characters)
        )
    return lines or [""]


def captured_lines(
    command: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    timestamp: str,
) -> list[str]:
    rows = [f"> {command}", "", "[stdout]"]
    rows.extend(wrap_exact(stdout, 128))
    rows.extend(["", "[stderr]"])
    rows.extend(wrap_exact(stderr, 128))
    rows.extend(["", f"Exit code: {exit_code}", f"Captured at {timestamp}"])
    return rows


def command_output(command: str, timeout: int) -> tuple[str, str, int]:
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return completed.stdout, completed.stderr, completed.returncode
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return stdout, stderr, 124


def render(command: str, stdout: str, stderr: str, exit_code: int) -> Image.Image:
    font = load_font(17)
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    rows = captured_lines(command, stdout, stderr, exit_code, timestamp)

    sample = Image.new("RGB", (10, 10))
    draw_sample = ImageDraw.Draw(sample)
    box = draw_sample.textbbox((0, 0), "M", font=font)
    cell_width = box[2] - box[0]
    line_height = max(22, box[3] - box[1] + 6)
    max_characters = max(48, min(128, max(len(line) for line in rows)))
    width = max(900, min(1440, max_characters * cell_width + 48))
    height = len(rows) * line_height + 40
    image = Image.new("RGB", (width, height), "#111827")
    draw = ImageDraw.Draw(image)
    y = 20
    for index, row in enumerate(rows):
        color = "#93c5fd" if index == 0 else "#e5e7eb"
        if row.startswith("[stderr]"):
            color = "#fca5a5"
        elif row.startswith("Exit code:") and exit_code != 0:
            color = "#fca5a5"
        elif row.startswith("Captured at"):
            color = "#9ca3af"
        draw.text((24, y), row, fill=color, font=font)
        y += line_height
    return image


def main() -> int:
    parser = argparse.ArgumentParser(description="Render real command output to a PNG.")
    parser.add_argument("--output", required=True, help="PNG path relative to the repository root")
    parser.add_argument("--command", required=True, help="Command to run and display")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()

    stdout, stderr, exit_code = command_output(args.command, args.timeout)
    image = render(args.command, stdout, stderr, exit_code)
    destination = Path(args.output)
    if not destination.is_absolute():
        destination = ROOT / destination
    result = save_png(image, destination.name, read_env())
    if result.status == "Failed":
        print(result.reason, file=sys.stderr)
        return 2
    if result.status == "Skipped":
        print(f"Skipped: {result.reason}")
        return 0
    print(
        f"Rendered captured output to {destination.relative_to(ROOT)} "
        f"with command exit code {exit_code}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
