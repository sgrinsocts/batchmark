"""CLI entry point for batchmark."""

import argparse
import sys
from pathlib import Path

from batchmark.config import load_config
from batchmark.reporter import write_report
from batchmark.runner import run_all


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchmark",
        description="Benchmark batch jobs with configurable concurrency.",
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to YAML config file.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output report format (default: text).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write report to file instead of stdout.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help="Override concurrency setting from config.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 1

    if args.concurrency is not None:
        config = config.model_copy(update={"concurrency": args.concurrency})

    summary = run_all(config)
    write_report(summary, fmt=args.fmt, output=args.output)

    return 0 if summary.failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
