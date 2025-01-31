import pathlib

from algokit_client_generator import generate_client


def update_approvals() -> None:
    examples = pathlib.Path(__file__).parent.parent / "examples"
    for app in [
        "arc56_test",
        "duplicate_structs",
        "structs",
        "helloworld",
        "lifecycle",
        "minimal",
        "nested",
        "nfd",
        "reti",
        "state",
        "voting",
        "zero_coupon_bond",
    ]:
        app_path = examples / app
        app_spec = app_path / "application.json"
        approved_path = app_path / "client.py"
        try:
            generate_client(app_spec, approved_path)
        except Exception as e:
            print(f"Error generating client for {app}: {e}")


if __name__ == "__main__":
    update_approvals()
