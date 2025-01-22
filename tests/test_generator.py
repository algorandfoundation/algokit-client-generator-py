import pathlib

import pytest

from algokit_client_generator import generate_client


@pytest.mark.parametrize(
    "app",
    [
        "nested",
        "arc56_test",
        "duplicate_structs",
        "nfd",
        "reti",
        "state",
        "helloworld",
        "lifecycle",
        "minimal",
        "voting",
        "global_state_struct",
    ],
)
def test_generate_clients(app: str) -> None:
    examples = pathlib.Path(__file__).parent.parent / "examples"
    app_path = examples / app
    app_spec = app_path / "application.json"
    generated_path = app_path / "client_generated.py"
    approved_path = app_path / "client.py"
    generate_client(app_spec, generated_path)
    assert generated_path.read_text() == approved_path.read_text()
