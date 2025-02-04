import pathlib

import pytest

from algokit_client_generator import generate_client


def to_camel_case(s: str) -> str:
    return "".join([x.capitalize() for x in s.split("_")])


@pytest.mark.parametrize(
    "app",
    [
        "arc56_test",
        "duplicate_structs",
        "structs",
        "hello_world",
        "lifecycle",
        "minimal",
        "nested",
        "nfd",
        "reti",
        "state",
        "voting_round",
        "zero_coupon_bond",
    ],
)
def test_generate_clients(app: str) -> None:
    examples = pathlib.Path(__file__).parent.parent / "examples"
    app_path = examples / app
    app_spec = app_path / f"{to_camel_case(app)}.arc32.json"
    generated_path = app_path / "client_generated.py"
    approved_path = app_path / "client.py"
    generate_client(app_spec, generated_path)
    assert generated_path.read_text() == approved_path.read_text()
