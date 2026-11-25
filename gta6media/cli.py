"""Unified CLI entry point: python -m gta6media <command> [options]."""

from __future__ import annotations

import argparse
import sys

from . import __version__


def main() -> None:
    ap = argparse.ArgumentParser(
        prog="gta6media",
        description="Organize, transcode and QC carved GTA VI Bink2 media.",
    )
    ap.add_argument("--version", action="version", version=f"gta6media {__version__}")
    ap.add_argument(
        "command",
        choices=["inventory", "classify", "extract", "convert", "qc", "inspect"],
        help="tool to run; pass --help after the command for its options",
    )
    args, rest = ap.parse_known_args()

    if args.command == "inventory":
        from .inventory import main as m
    elif args.command == "classify":
        from .classify import main as m
    elif args.command == "extract":
        from .extract import main as m
    elif args.command == "convert":
        from .convert import main as m
    elif args.command == "qc":
        from .qc import main as m
    else:
        from .inspect import main as m

    sys.argv = [sys.argv[0], *rest]
    m()


if __name__ == "__main__":
    main()
