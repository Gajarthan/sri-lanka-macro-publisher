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
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""

    configure_logging()
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "run-all":
            statuses = run_all()
        elif args.command == "run-source":
            statuses = [run_source(args.source_name)]
        else:
            statuses = healthcheck()
    except Exception:
        logging.exception("Pipeline execution failed")
        return 1

    print(json.dumps([status.model_dump(mode="json") for status in statuses], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
