import pathlib

from algokit_client_generator import generate_client


def update_approvals() -> None:
    examples = pathlib.Path(__file__).parent.parent / "examples"
    for app in ["helloworld", "lifecycle", "minimal", "state", "voting"]:
        app_path = examples / app
        app_spec = app_path / "application.json"
        approved_path = app_path / "client.py"
        generate_client(app_spec, approved_path)


if __name__ == "__main__":
    update_approvals()
