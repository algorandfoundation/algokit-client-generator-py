import pathlib

from algokit_client_generator import generate_client


def test_generate_clients() -> None:
    examples = pathlib.Path(__file__).parent.parent / "examples"
    for path in examples.iterdir():
        if path.is_dir():
            app_spec = path / "application.json"
            generate_client(app_spec, path / "client_generated.py")
