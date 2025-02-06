import pathlib
from itertools import chain, product

from inflection import camelize
from algokit_client_generator import generate_client


def update_approvals() -> None:
    artifacts = pathlib.Path(__file__).parent.parent / "examples" / "smart_contracts" / "artifacts"
    arc32_apps = [
        "duplicate_structs",
        "hello_world",
        "lifecycle",
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
        app_spec = app_path / f"{camelize(app)}.{extension}.json"
        approved_path = app_path / f"{app}_client.py"
        try:
            generate_client(app_spec, approved_path)
        except Exception as e:
            print(f"Error generating client for {app}: {e}")


if __name__ == "__main__":
    update_approvals()
