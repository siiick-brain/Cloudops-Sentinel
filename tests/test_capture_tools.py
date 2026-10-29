from PIL import Image

from scripts import capture_support
from scripts.terminal_shot import captured_lines, wrap_exact


def test_wrap_exact_preserves_all_command_output_characters() -> None:
    output = "first line  \nsecond line"
    wrapped = wrap_exact(output, 7)

    assert "".join(wrapped).replace("\n", "") == output.replace("\n", "")
    assert wrapped[0] == "first l"
    assert wrapped[1] == "ine  "


def test_terminal_capture_includes_command_streams_exit_code_and_timestamp() -> None:
    rows = captured_lines(
        "python check.py",
        "standard output",
        "standard error",
        2,
        "2026-10-29T12:00:00+00:00",
    )

    assert rows[0] == "> python check.py"
    assert "standard output" in rows
    assert "standard error" in rows
    assert "Exit code: 2" in rows
    assert rows[-1] == "Captured at 2026-10-29T12:00:00+00:00"


def test_capture_does_not_replace_selected_dashboard_image(tmp_path, monkeypatch) -> None:
    original = b"selected screenshot"
    destination = tmp_path / "grafana-golden-signals.png"
    destination.write_bytes(original)
    monkeypatch.setattr(capture_support, "IMAGE_DIR", tmp_path)

    result = capture_support.save_png(
        Image.new("RGB", (10, 10), "white"),
        destination.name,
        {},
    )

    assert result.status == "Skipped"
    assert destination.read_bytes() == original
