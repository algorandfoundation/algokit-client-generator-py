import argparse
import logging
import sys
from pathlib import Path

from algokit_client_generator.writer import generate_client

logger = logging.getLogger(__name__)


class ArgumentError(Exception):
    def __init__(self, message: str):
        self.message = message


def get_args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generates typed python clients from an Algorand ARC-0032 specification file."
    )

    parser.add_argument(
        "-a",
        "--app_spec",
        default=".",
        type=Path,
        help="The path to an application.json or a directory if using --walk. Defaults to current directory",
    )
    parser.add_argument(
        "-o", "--output", default="client_generated.py", type=Path, help="The output filename for the generated client"
    )
    parser.add_argument(
        "-w",
        "--walk",
        action="store_true",
        help="Walk the input path recursively, generating a client for each application.json found",
    )
    parser.add_argument(
        "-p",
        "--preserve-names",
        action="store_true",
        help="Preserve original names for structs and methods",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["full", "minimal"],
        default="full",
        help="Generate client in specified mode. The 'full' mode includes all features, "
        "'minimal' generates a smaller client without deployment features",
    )
    return parser


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


def walk_dir(path: Path, output: Path, *, preserve_names: bool = False, mode: str = "full") -> None:
    for child in path.iterdir():
        if child.is_dir():
            walk_dir(child, output, preserve_names=preserve_names, mode=mode)
        elif child.name.lower() == "application.json":
            generate_client(child, child.parent / output, preserve_names=preserve_names, mode=mode)


def process(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    app_spec: Path = args.app_spec
    output: Path = args.output
    if not app_spec.exists():
        raise ArgumentError(f"Application Specification not found: {app_spec}")

    if args.walk:
        if not app_spec.is_dir():
            raise ArgumentError(
                f"Application specification must be a path to a directory, when using the --walk option: {app_spec}"
            )
        if output.is_absolute():
            raise ArgumentError(f"Output must be a relative path when using the --walk option: {output}")
        walk_dir(args.app_spec, args.output, preserve_names=args.preserve_names, mode=args.mode)
    elif len(sys.argv) == 1:  # if user invokes with no arguments display help
        parser.print_usage()
    else:
        if not app_spec.is_file():
            raise ArgumentError(f"Application Specification must be a path to an application.json: {app_spec}")
        generate_client(app_spec, output, preserve_names=args.preserve_names, mode=args.mode)


def main() -> None:
    configure_logging()
    parser = get_args_parser()
    try:
        process(parser)
    except ArgumentError as ex:
        logger.error(ex.message)
