import sys
from pathlib import Path

from algokit_client_generator.generator import GenerationSettings
from algokit_client_generator.writer import generate_client

DEFAULT_CLIENT = "client_generated.py"


def walk_dir(path: Path, output_name: str, settings: GenerationSettings) -> None:
    for child in path.iterdir():
        if child.is_dir():
            walk_dir(child, output_name, settings)
        elif child.name.lower() == "application.json":
            generate_client(child, child.parent / output_name, settings)


def main() -> None:
    # TODO: proper CLI parsing
    settings = GenerationSettings(max_line_length=120)

    if "--scan" in sys.argv:
        walk_dir(Path(".").absolute(), DEFAULT_CLIENT, settings)
    elif len(sys.argv) > 1:
        input_path = Path(sys.argv[1]).absolute()
        if not input_path.exists():
            print(f"{input_path} not found", file=sys.stderr)
            return
        elif input_path.is_dir():
            print(f"{input_path} is not a file", file=sys.stderr)
            return
        if len(sys.argv) > 2:
            output_path = Path(sys.argv[2])
        else:
            output_path = input_path.parent / DEFAULT_CLIENT
        generate_client(input_path, output_path, settings)
    else:
        print("usage: algokit-client-generator --scan")
        print("       Scans current directory recursively and outputs a typed client for each application.json found")
        print()
        print("usage: algokit-client-generator path/to/application.json")
        print(f"       Outputs a typed client to path/to/{DEFAULT_CLIENT}")
        print()
        print("usage: algokit-client-generator path/to/application.json my_client.py")
        print("       Outputs a typed client to my_client.py")
        return
