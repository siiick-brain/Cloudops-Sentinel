import subprocess
import sys

TERMS = ["ag" + "ent", "pro" + "mpt", "sk" + "ill", "cl" + "aude", "co" + "pilot", "chat" + "gpt"]
EXPECTED_AUTHOR = "devasoka38@gmail.com"


def tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    return [path.decode("utf-8") for path in result.stdout.split(b"\0") if path]


def main() -> int:
    errors = []
    for path in tracked_paths():
        try:
            content = open(path, "rb").read().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lowered = content.casefold()
        if any(term in lowered for term in TERMS):
            errors.append(f"Prohibited text found in {path}")
    head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        check=False,
        capture_output=True,
    )
    if head.returncode != 0:
        errors.append("Commit history check requires a committed HEAD")
    else:
        commit = subprocess.run(
            ["git", "log", "-1", "HEAD", "--format=%B"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if any(term in commit.stdout.casefold() for term in TERMS):
            errors.append("Prohibited text found in HEAD commit message")
        authors = subprocess.run(
            ["git", "log", "HEAD", "--format=%ae"],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        invalid = [email for email in authors.stdout.splitlines() if email != EXPECTED_AUTHOR]
        if invalid:
            errors.append("A commit has an author email outside the configured owner identity")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Tracked text, HEAD commit message and author emails passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
