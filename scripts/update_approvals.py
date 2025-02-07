import pathlib
from itertools import chain, product

from algokit_client_generator import generate_client
from algokit_client_generator.utils import to_pascal_case, to_snake_case


def update_approvals() -> None:
    artifacts = pathlib.Path(__file__).parent.parent / "examples" / "smart_contracts" / "artifacts"
    arc32_apps = [
        "duplicate_structs",
        "hello_world",
        "life_cycle",
        "minimal",
        "state",
        "voting_round",
    ]
    arc56_apps = [
        "arc56_test",
        "structs",
        "nested",
        "nfd",
        "reti",
        "zero_coupon_bond",
    ]

    for app, extension in chain(product(arc32_apps, ["arc32"]), product(arc56_apps, ["arc56"])):
        app_path = artifacts / app
        app_spec = app_path / f"{to_pascal_case(app)}.{extension}.json"
        approved_path = app_path / f"{to_snake_case(app)}_client.py"
        try:
            generate_client(app_spec, approved_path)
        except Exception as e:
            print(f"Error generating client for {app}: {e}")


if __name__ == "__main__":
    update_approvals()
