import pathlib

from algokit_client_generator import generate_client


def test_generate_clients() -> None:
    examples = pathlib.Path(__file__).parent.parent / "examples"
    for app in ["helloworld", "lifecycle", "state", "voting"]:
        app_path = examples / app
        app_spec = app_path / "application.json"
        generated_path = app_path / "client_generated.py"
        approved_path = app_path / "client.py"
        generate_client(app_spec, generated_path)
        assert generated_path.read_text() == approved_path.read_text()
