import pathlib

from algokit_client_generator import generate_client


def to_camel_case(s: str) -> str:
    return "".join([x.capitalize() for x in s.split("_")])


def update_approvals() -> None:
    artifacts = pathlib.Path(__file__).parent.parent / "examples" / "smart_contracts" / "artifacts"
    # TODO: Uncomment all apps.
    for app in [
        # "arc56_test",
        # "duplicate_structs",
        # "structs",
        "hello_world",
        "lifecycle",
        "minimal",
        # "nested",
        # "nfd",
        # "reti",
        "state",
        "voting_round",
        # "zero_coupon_bond",
    ]:
        app_path = artifacts / app
        app_spec = app_path / f"{to_camel_case(app)}.arc32.json"
        approved_path = app_path / f"{app}_client.py"
        try:
            generate_client(app_spec, approved_path)
        except Exception as e:
            print(f"Error generating client for {app}: {e}")


if __name__ == "__main__":
    update_approvals()
