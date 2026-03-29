"""CLI entrypoint for the macro publisher."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from macro_publisher.logging import configure_logging
from macro_publisher.pipeline.healthcheck import healthcheck
from macro_publisher.pipeline.run_all import run_all
from macro_publisher.pipeline.run_source import run_source


def build_parser() -> argparse.ArgumentParser:
    """Build the project CLI parser."""

    parser = argparse.ArgumentParser(prog="macro-publisher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("run-all", help="Run all source adapters and publish outputs.")

    run_source_parser = subparsers.add_parser("run-source", help="Run one source adapter.")
    run_source_parser.add_argument("source_name", help="Registered source name.")

    subparsers.add_parser("healthcheck", help="Run source checks without writing outputs.")

    subparsers.add_parser("generate-readme", help="Regenerate README.md from current data.")
    subparsers.add_parser("generate-daily-report", help="Generate DAILY_REPORT.md.")
    subparsers.add_parser("generate-leaderboard", help="Generate LEADERBOARD.md.")
    subparsers.add_parser("generate-post", help="Generate POST.txt social thread.")
    subparsers.add_parser("generate-all-reports", help="Generate all reports.")
    subparsers.add_parser("record-history", help="Append a pipeline history row.")
    return parser


def _generate_all_reports() -> None:
    from macro_publisher.reports.daily_report import generate_daily_report
    from macro_publisher.reports.leaderboard import generate_leaderboard
    from macro_publisher.reports.post import generate_post
    from macro_publisher.reports.readme import generate_readme

    generate_readme()
    generate_daily_report()
    generate_leaderboard()
    generate_post()


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "run-all":
            statuses = run_all()
            print(json.dumps([s.model_dump(mode="json") for s in statuses], indent=2))
        elif args.command == "run-source":
            statuses = [run_source(args.source_name)]
            print(json.dumps([s.model_dump(mode="json") for s in statuses], indent=2))
        elif args.command == "healthcheck":
            statuses = healthcheck()
            print(json.dumps([s.model_dump(mode="json") for s in statuses], indent=2))
        elif args.command == "generate-readme":
            from macro_publisher.reports.readme import generate_readme

            path = generate_readme()
            print(f"Generated {path}")
        elif args.command == "generate-daily-report":
            from macro_publisher.reports.daily_report import generate_daily_report

            path = generate_daily_report()
            print(f"Generated {path}")
        elif args.command == "generate-leaderboard":
            from macro_publisher.reports.leaderboard import generate_leaderboard

            path = generate_leaderboard()
            print(f"Generated {path}")
        elif args.command == "generate-post":
            from macro_publisher.reports.post import generate_post

            path = generate_post()
            print(f"Generated {path}")
        elif args.command == "generate-all-reports":
            _generate_all_reports()
            print("Generated all reports.")
        elif args.command == "record-history":
            from macro_publisher.reports.pipeline_history import append_run

            path = append_run()
            print(f"Appended pipeline history row to {path}")
        else:
            statuses = healthcheck()
            print(json.dumps([s.model_dump(mode="json") for s in statuses], indent=2))
    except Exception:
        logging.exception("Pipeline execution failed")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
