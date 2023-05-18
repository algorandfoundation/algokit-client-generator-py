import sys
from pathlib import Path

from algokit_client_generator.generator import GenerationSettings
from algokit_client_generator.writer import generate_client


def walk_dir(path: Path, output_name: str, settings: GenerationSettings) -> None:
    for child in path.iterdir():
        if child.is_dir():
            walk_dir(child, output_name, settings)
        elif child.name.lower() == "application.json":
            generate_client(child, child.parent / output_name, settings)


def main() -> None:
    # TODO: proper CLI parsing
    args = dict(enumerate(sys.argv))
    input_path = Path(args.get(1, ".")).absolute()
    output = args.get(2, "client_generated.py")

    settings = GenerationSettings(max_line_length=120)

    if not input_path.exists():
        raise Exception(f"{input_path} not found")

    if input_path.is_dir():
        walk_dir(input_path, output, settings)
    else:
        output_path = Path(output)
        if not output_path.is_absolute():
            output_path = input_path.parent / output
        generate_client(input_path, output_path, settings)


if __name__ == "__main__":
    main()
