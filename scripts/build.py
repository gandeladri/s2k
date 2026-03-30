import sys

from build_windows import build_windows
from validate_project import validate_project


USAGE = """Usage:
  python scripts/build.py
  python scripts/build.py --windows
  python scripts/build.py --validate

Notes:
  - Windows builds are intended for Windows.
  - --validate only runs project validation checks.
"""


def main(argv: list[str]) -> int:
    args = set(argv[1:])

    if "--help" in args or "-h" in args:
        print(USAGE.strip())
        return 0

    if "--validate" in args:
        return validate_project()

    selected_windows = "--windows" in args or not args

    exit_codes: list[int] = []

    if selected_windows:
        print("=== Windows build ===")
        exit_codes.append(build_windows())

    return max(exit_codes, default=0)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
