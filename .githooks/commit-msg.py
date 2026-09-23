#!/usr/bin/env python3
import re
import sys


def main():
    commit_msg_file = sys.argv[1]

    with open(commit_msg_file, "r", encoding="utf-8") as f:
        commit_msg = f.read().strip()

    # https://github.com/commitizen/conventional-commit-types/blob/master/index.json
    pattern = r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([a-zA-Z0-9_-]+\))?!?: .+"
    match = re.match(pattern, commit_msg)

    if not match:
        print("❌ Error: Invalid commit message format.")
        print("   Must match: <type>(<scope>): <message>")
        print(f"   Your message: '{commit_msg}'")
        sys.exit(1)

    allowed_scopes = ["json-plugin", "format"]
    scope = match.group(2)

    if scope and scope not in allowed_scopes:
        print(f"❌ Error: Unrecognized scope '{scope}'.")
        print(f"   Allowed scopes for plugins: {', '.join(allowed_scopes)}")
        print(
            "   Omit the scope entirely for core framework changes (e.g., 'feat: add X')."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
