"""Check Git publication candidates for common accidental sensitive additions.

This heuristic complements manual review; it cannot establish publishing rights
or recognize every identifier or secret. It prints rule names, never matched values.
"""

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "private network address": re.compile(r"\b(?:10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "common token format": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[A-Z0-9]{16})\b"),
    "personal Windows path": re.compile(r"[A-Za-z]:[\\/]Users[\\/](?!Public\b)[^\s\"']+", re.I),
    "personal Unix path": re.compile(r"/(?:home|Users)/[A-Za-z0-9_.-]+/"),
}
BAD_SUFFIXES = {".doc", ".docx", ".xls", ".xlsx", ".pdf", ".db", ".sqlite", ".log", ".pem", ".key", ".pfx", ".crt", ".zip"}


def main():
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True, capture_output=True,
    )
    files = sorted(set(result.stdout.decode("utf-8").strip("\0").split("\0")) - {""})
    problems = []
    for name in files:
        path = ROOT / name
        if path.is_symlink():
            problems.append((name, "symlink requires manual review"))
            continue
        if path.suffix.lower() in BAD_SUFFIXES or path.name.startswith(".env"):
            problems.append((name, "excluded artifact type"))
        if path.suffix.lower() == ".png":
            if name != "docs/demo.png":
                problems.append((name, "unreviewed image"))
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            problems.append((name, "unreviewed binary or unreadable file"))
            continue
        for label, pattern in RULES.items():
            if pattern.search(content):
                problems.append((name, label))
        for address in re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", content):
            if not address.lower().endswith(("@example.test", "@example.com")):
                problems.append((name, "non-example email address"))
    for name, reason in problems:
        print(f"REVIEW: {name}: {reason}")
    print(f"Publication candidates checked: {len(files)}; findings: {len(problems)}")
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
