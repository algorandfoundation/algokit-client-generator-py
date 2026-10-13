import pathlib
from itertools import chain, product

from algokit_client_generator import generate_client
from algokit_client_generator.utils import to_pascal_case, to_snake_case
from scripts._helpers import enable_mypy


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
        "state",
        "nested",
        "nfd",
        "reti",
        "zero_coupon_bond",
    ]

    # Generate both full and minimal clients for each app
    modes = ["full", "minimal"]

    for app, extension, mode in chain(product(arc32_apps, ["arc32"], modes), product(arc56_apps, ["arc56"], modes)):
        app_path = artifacts / app
        app_spec = app_path / f"{to_pascal_case(app)}.{extension}.json"

        # Generate filename based on mode
        if mode == "minimal":
            approved_path = app_path / f"{to_snake_case(app)}_{extension}_client_minimal.py"
        else:
            approved_path = app_path / f"{to_snake_case(app)}_{extension}_client.py"

        try:
            generate_client(app_spec, approved_path, mode=mode)
            enable_mypy(approved_path)
        except Exception as e:
            print(f"Error generating {mode} client for {app}: {e}")


if __name__ == "__main__":
    update_approvals()
