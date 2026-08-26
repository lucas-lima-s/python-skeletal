import argparse
import json
import sys
from collections.abc import Sequence

from skeletal import __version__
from skeletal.config import Settings, get_settings
from skeletal.logging_setup import configure_logging


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        message = f"invalid int value: {value!r}"
        raise argparse.ArgumentTypeError(message) from exc
    if parsed < 1:
        message = f"iterations must be >= 1, got {parsed}"
        raise argparse.ArgumentTypeError(message)
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skeletal", description="skeletal project template CLI")
    parser.add_argument("--version", action="store_true", help="print the version and exit")

    subparsers = parser.add_subparsers(dest="command")

    info_parser = subparsers.add_parser("info", help="show resolved settings")
    info_parser.add_argument("--json", action="store_true", help="emit settings as JSON")

    run_parser = subparsers.add_parser("run", help="run the demo workload")
    run_parser.add_argument(
        "--iterations", type=_positive_int, default=1, help="number of iterations to run"
    )

    return parser


def _print_info(settings: Settings, *, as_json: bool) -> None:
    dump = settings.redacted_dump()
    if as_json:
        print(json.dumps(dump, indent=2, sort_keys=True))
        return
    width = max(len(key) for key in dump)
    for key in sorted(dump):
        print(f"{key.ljust(width)}: {dump[key]}")


def _run_workload(iterations: int) -> None:
    settings = get_settings()
    logger = configure_logging(settings)
    for iteration in range(1, iterations + 1):
        logger.info("iteration %d/%d", iteration, iterations)


def _run_command(command: str, args: argparse.Namespace) -> int:
    if command == "info":
        _print_info(get_settings(), as_json=args.json)
    elif command == "run":
        _run_workload(args.iterations)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"skeletal {__version__}")
        return 0

    if args.command is None:
        parser.print_usage(sys.stderr)
        return 2

    try:
        return _run_command(args.command, args)
    except KeyboardInterrupt:
        return 130
    except Exception:
        logger = configure_logging(get_settings())
        logger.exception("unhandled error while running %r", args.command)
        print("skeletal: unhandled error, see logs for details", file=sys.stderr)
        return 1
