import pathlib
from itertools import chain, product

import pytest

from algokit_client_generator import generate_client
from algokit_client_generator.utils import to_pascal_case, to_snake_case
from scripts._helpers import enable_mypy


@pytest.mark.parametrize(
    ("app", "extension"),
    chain(
        product(
            [
                "duplicate_structs",
                "hello_world",
                "life_cycle",
                "minimal",
                "state",
                "voting_round",
            ],
            ["arc32"],
        ),
        product(
            [
                "arc56_test",
                "structs",
                "nested",
                "nfd",
                "reti",
                "zero_coupon_bond",
            ],
            ["arc56"],
        ),
    ),
)
def test_generate_clients(app: str, extension: str) -> None:
    artifacts = pathlib.Path(__file__).parent.parent / "examples" / "smart_contracts" / "artifacts"
    app_path = artifacts / app
    app_spec = app_path / f"{to_pascal_case(app)}.{extension}.json"
    generated_full_client_path = app_path / f"client_generated_{extension}.py"
    approved_full_client_path = app_path / f"{to_snake_case(app)}_{extension}_client.py"
    generated_minimal_client_path = app_path / f"client_generated_minimal_{extension}.py"
    approved_minimal_client_path = app_path / f"{to_snake_case(app)}_{extension}_client_minimal.py"

    generate_client(app_spec, generated_full_client_path)
    enable_mypy(generated_full_client_path)
    assert generated_full_client_path.read_text() == approved_full_client_path.read_text()

    generate_client(app_spec, generated_minimal_client_path, mode="minimal")
    enable_mypy(generated_minimal_client_path)
    assert generated_minimal_client_path.read_text() == approved_minimal_client_path.read_text()
