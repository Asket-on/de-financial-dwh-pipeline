from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".local", "__pycache__", ".pytest_cache"}
SKIP_SUFFIXES = {".pyc", ".sqlite", ".sqlite3"}

PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "generic secret assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?key|secret|token|password)\b\s*[:=]\s*[\"']?([^\s\"']+)"
    ),
    "private IPv4 address": re.compile(
        r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
    ),
}

ALLOWED_ASSIGNMENT_VALUES = {
    "change_me",
    "demo_user",
    "localhost",
}


def iter_text_files() -> list[Path]:
    return [
        path
        for path in PROJECT_ROOT.rglob("*")
        if path.is_file()
        and not any(part in SKIP_DIRS for part in path.parts)
        and path.suffix.lower() not in SKIP_SUFFIXES
    ]


def scan_file(path: Path) -> list[str]:
    findings = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    relative_path = path.relative_to(PROJECT_ROOT)

    for line_number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in PATTERNS.items():
            for match in pattern.finditer(line):
                if label == "generic secret assignment":
                    value = match.group(1).rstrip(",")
                    if value in ALLOWED_ASSIGNMENT_VALUES or "os.getenv(" in line:
                        continue
                findings.append(f"{relative_path}:{line_number}: {label}")

    return findings


def main() -> int:
    findings = [
        finding
        for path in iter_text_files()
        for finding in scan_file(path)
    ]

    if findings:
        print("Potential secrets found:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("secrets_audit=passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

