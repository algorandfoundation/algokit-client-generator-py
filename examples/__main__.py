import importlib
import json
import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import algokit_utils

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)-10s: %(message)s"
)
logger = logging.getLogger(__name__)
root_path = Path(__file__).parent


@contextmanager
def cwd(path: Path) -> Generator[None, None, None]:
    old_pwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_pwd)


def to_json(app_spec: algokit_utils.ApplicationSpecification) -> str:
    app_spec_dict = app_spec.dictify()
    # beaker always outputs an empty string by default for the schema "descr" field, however this field is optional
    # so remove these keys if they are an empty string so optional descr fields are covered
    for scope in ("global", "local"):
        for reservation in ("declared", "reserved"):
            state_dict = app_spec_dict["schema"][scope][reservation]
            for _field, field_spec in state_dict.items():
                if not field_spec.get("descr"):
                    del field_spec["descr"]
    return json.dumps(app_spec_dict, indent=4)


def main() -> None:
    example_dirs = filter(
        lambda file: file.is_dir() and "__" not in file.name, root_path.glob("*")
    )
    for example in example_dirs:
        try:
            logger.info(f"Building example {example.name}")
            with cwd(root_path):
                evaluated_file = importlib.import_module(
                    f"examples.{example.name}.{example.name}"
                )
            app = evaluated_file.app
            logger.info(f"  Building app {app.name}")
            app_spec = app.build()
            logger.info(f"  Writing {example.name}/application.json")
            (example / "application.json").write_text(
                to_json(app_spec), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(f"Skipping example {example.name} due to error: {e}")


if __name__ == "__main__":
    main()
