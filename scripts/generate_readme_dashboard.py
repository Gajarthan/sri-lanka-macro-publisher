"""Regenerate the bounded README dashboard block from published data."""

from __future__ import annotations

import sys

from macro_publisher.reports.readme_dashboard import generate_readme_dashboard


def main() -> int:
    path = generate_readme_dashboard()
    print(f"Updated README dashboard block in {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
