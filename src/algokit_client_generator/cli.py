import argparse
import sys
from pathlib import Path

from algokit_client_generator.generator import GenerationSettings
from algokit_client_generator.writer import generate_client

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
args = parser.parse_args()

DEFAULT_CLIENT = "client_generated.py"


def walk_dir(path: Path, output: Path, settings: GenerationSettings) -> None:
    for child in path.iterdir():
        if child.is_dir():
            walk_dir(child, output, settings)
        elif child.name.lower() == "application.json":
            generate_client(child, child.parent / output, settings)


def main() -> None:
    settings = GenerationSettings(max_line_length=120)
    app_spec: Path = args.app_spec
    output: Path = args.output
    if not app_spec.exists():
        print(f"{app_spec} not found", file=sys.stderr)
        return

    if args.walk:
        if not app_spec.is_dir():
            print(f"{app_spec} must be a path to a directory, when using the --walk option", file=sys.stderr)
            return
        if output.is_absolute():
            print(f"{output} must be a relative path, when using the --walk option", file=sys.stderr)
            return
        walk_dir(args.app_spec, args.output, settings)
    elif len(sys.argv) == 1:  # if user invokes with no arguments display help
        parser.print_usage()
    else:
        if not app_spec.is_file():
            print(f"{app_spec} must be a path to an application.json", file=sys.stderr)
            return
        generate_client(app_spec, output, settings)
