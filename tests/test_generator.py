import pathlib

from algokit_client_generator import generate_client


def test_generate_clients() -> None:
    examples = pathlib.Path(__file__).parent.parent / "examples"
    for app in ["helloworld", "lifecycle", "state", "voting"]:
        app_path = examples / app
        app_spec = app_path / "application.json"
        generate_client(app_spec, app_path / "client_generated.py")
