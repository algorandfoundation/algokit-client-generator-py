import logging
import pathlib
import subprocess
from pathlib import Path

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)-10s: %(message)s"
)
logger = logging.getLogger(__name__)
root_path = Path(__file__).parent


def to_camel_case(s: str) -> str:
    return "".join([x.capitalize() for x in s.split("_")])


def main() -> None:
    smart_contracts = pathlib.Path(__file__).parent / "smart_contracts"
    artifacts = smart_contracts / "artifacts"

    # TODO: Uncomment all apps.
    for app in [
        # "duplicate_structs",
        "hello_world",
        "lifecycle",
        "minimal",
        "state",
        "voting_round",
    ]:
        app_path = smart_contracts / app / "contract.py"
        app_artifacts = artifacts / app
        try:
            subprocess.run(
                [
                    "algokit",
                    "--no-color",
                    "compile",
                    "python",
                    app_path.absolute(),
                    f"--out-dir={app_artifacts}",
                    "--output-arc32",
                    "--no-output-teal",
                    "--no-output-source-map",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True,
            )
        except Exception as e:
            print(f"Error compiling contract for app {app}: {e}")

    # TODO: Uncomment all apps.
    for app in [
        # "duplicate_structs",
        "structs",
        "nested",
    ]:
        app_path = smart_contracts / app / "contract.py"
        app_artifacts = artifacts / app
        try:
            subprocess.run(
                [
                    "algokit",
                    "--no-color",
                    "compile",
                    "python",
                    app_path.absolute(),
                    f"--out-dir={app_artifacts}",
                    "--output-arc56",
                    "--no-output-arc32",
                    "--no-output-teal",
                    "--no-output-source-map",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=True,
            )
        except Exception as e:
            print(f"Error compiling contract for app {app}: {e}")


if __name__ == "__main__":
    main()
