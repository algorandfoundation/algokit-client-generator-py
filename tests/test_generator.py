import pathlib
from itertools import chain, product

import pytest

from algokit_client_generator import generate_client


def to_camel_case(s: str) -> str:
    return "".join([x.capitalize() for x in s.split("_")])


@pytest.mark.parametrize(
    "app, extension",
    chain(product([
        "duplicate_structs",
        "hello_world",
        "lifecycle",
        "minimal",
        "state",
        "voting_round",
    ], "arc32"), product([
        "arc56_test",
        "structs",
        "nested",
        "nfd",
        "reti",
        "zero_coupon_bond",
    ], "arc56"))
)
def test_generate_clients(app: str, extension: str) -> None:
    examples = pathlib.Path(__file__).parent.parent / "examples"
    app_path = examples / app
    app_spec = app_path / f"{to_camel_case(app)}.{extension}.json"
    generated_path = app_path / "client_generated.py"
    approved_path = app_path / "client.py"
    generate_client(app_spec, generated_path)
    assert generated_path.read_text() == approved_path.read_text()
